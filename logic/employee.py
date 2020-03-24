# -*- coding: utf-8 -*-
import csv
import json
import os.path
import logging

from google.cloud import ndb


import config
from errors import NoSuchEmployee
from logic.secret import get_secret
from logic.toggle import set_toggle_state
from models import Employee
from models import Love
from models import LoveCount
from models.toggle import LOVE_SENDING_ENABLED
from models.mysql import MySql


def csv_import_file():
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '../import/employees.csv'
    )


def load_employees_from_csv():
    employee_dicts = _get_employee_info_from_csv()
    set_toggle_state(LOVE_SENDING_ENABLED, False)
    _update_employees(employee_dicts)
    set_toggle_state(LOVE_SENDING_ENABLED, True)


def _get_employee_info_from_csv():
    logging.info('Reading employees from csv file...')
    employees = csv.DictReader(open(csv_import_file()))
    logging.info('Done reading employees from csv file.')
    return employees


def _get_employee_info_from_s3():
    from boto import connect_s3
    from boto.s3.key import Key

    logging.info('Reading employees file from S3...')
    key = Key(
        connect_s3(
            aws_access_key_id=get_secret('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=get_secret('AWS_SECRET_ACCESS_KEY'),
        ).get_bucket(config.S3_BUCKET),
        'employees.json',
    )
    employee_dicts = json.loads(key.get_contents_as_string())
    logging.info('Done reading employees file from S3.')
    return employee_dicts


def _update_employees(employee_dicts):
    """Given a JSON string in the format "[{employee info 1}, {employee info 2}, ...]",
    create new employee records and update existing records as necessary.

    Then determine whether any employees have been terminated since the last update,
    and mark these employees as such.
    """
    logging.info('Updating employees...')

    db_employee_dict = {
        employee.username: employee
        for employee in Employee.query()
    }

    all_employees, new_employees = [], []
    current_usernames = set()
    for d in employee_dicts:
        existing_employee = db_employee_dict.get(d['username'])
        if existing_employee is None:
            new_employee = Employee.create_from_dict(d, persist=False)
            all_employees.append(new_employee)
            new_employees.append(new_employee)
        elif existing_employee.is_employee_data_changed(d, is_terminated=False):
            existing_employee.update_from_dict(d)
            all_employees.append(existing_employee)

        current_usernames.add(d['username'])
        logging.info('Processed {} employees'.format(len(all_employees)))

    # Only updates the changed and new employees data
    ndb.put_multi(all_employees)

    # Figure out if there are any employees in the DB that aren't in the S3
    # dump. These are terminated employees, and we need to mark them as such.
    db_usernames = set(db_employee_dict.keys())

    terminated_usernames = db_usernames - current_usernames
    terminated_employees = []
    for username in terminated_usernames:
        employee = db_employee_dict[username]

        # Only updating non-terminated employees
        if not employee.terminated:
            employee.terminated = True
            terminated_employees.append(employee)
    ndb.put_multi(terminated_employees)

    logging.info('Done updating employees.')


def combine_employees(old_username, new_username):
    set_toggle_state(LOVE_SENDING_ENABLED, False)

    old_employee_key = Employee.query(Employee.username == old_username).get(keys_only=True)
    new_employee_key = Employee.query(Employee.username == new_username).get(keys_only=True)
    if not old_employee_key:
        raise NoSuchEmployee(old_username)
    elif not new_employee_key:
        raise NoSuchEmployee(new_username)

    # First, we need to update the actual instances of Love sent to/from the old employee
    logging.info('Reassigning {}\'s love to {}...'.format(old_username, new_username))

    love_to_save = []

    # Reassign all love sent FROM old_username
    for sent_love in Love.query(Love.sender_key == old_employee_key).iter():
        sent_love.sender_key = new_employee_key
        love_to_save.append(sent_love)

    # Reassign all love sent TO old_username
    for received_love in Love.query(Love.recipient_key == old_employee_key).iter():
        received_love.recipient_key = new_employee_key
        love_to_save.append(received_love)

    ndb.put_multi(love_to_save)
    logging.info('Done reassigning love.')

    # Second, we need to update the LoveCount table
    logging.info('Updating LoveCount table...')

    love_counts_to_delete, love_counts_to_save = [], []

    for old_love_count in LoveCount.query(ancestor=old_employee_key).iter():
        # Try to find a corresponding row for the new employee
        new_love_count = LoveCount.query(
            ancestor=new_employee_key).filter(LoveCount.week_start == old_love_count.week_start).get()

        if new_love_count is None:
            # If there's no corresponding row for the new user, create one
            new_love_count = LoveCount(
                parent=new_employee_key,
                received_count=old_love_count.received_count,
                sent_count=old_love_count.sent_count,
                week_start=old_love_count.week_start
            )
        else:
            # Otherwise, combine the two rows
            new_love_count.received_count += old_love_count.received_count
            new_love_count.sent_count += old_love_count.sent_count

        # You `delete` keys but you `put` entities... Google's APIs are weird
        love_counts_to_delete.append(old_love_count.key)
        love_counts_to_save.append(new_love_count)

    ndb.delete_multi(love_counts_to_delete)
    ndb.put_multi(love_counts_to_save)
    logging.info('Done updating LoveCount table.')

    # Now we can delete the old employee
    logging.info('Deleting employee {}...'.format(old_username))
    old_employee_key.delete()
    logging.info('Done deleting employee.')

    set_toggle_state(LOVE_SENDING_ENABLED, True)


def employees_matching_prefix(prefix):
    """Returns a list of (full name, username) tuples for users that match the given prefix."""
    if not prefix:
        return []

    with MySql().db.connect() as conn:
        # Execute the query and fetch all results
        results = conn.execute(
            """SELECT * FROM employee_search where first_name like '{0}%%' or last_name like '{0}%%' or username like '{0}%%'
            or CONCAT(first_name, ' ', last_name) like '{0}%%';""".format(prefix)
        ).fetchall()
    user_tuples = set()

    for r in results:
        username, full_name = None, None
        full_name = r[1] + ' ' + r[2]
        username = r[0]
        if username is not None and full_name is not None:
            photo_url = r[4]
            user_tuples.add((full_name, username, photo_url))

    user_tuples = list(user_tuples)
    user_tuples.sort()
    return user_tuples


def load_employees():
    employee_dicts = _get_employee_info_from_s3()
    set_toggle_state(LOVE_SENDING_ENABLED, False)
    _update_employees(employee_dicts)
    set_toggle_state(LOVE_SENDING_ENABLED, True)


def load_employees_into_mysql():
    """Always truncates table and inserts all employees from datastore that are not terminated."""
    employees = [
        (
            employee.username,
            employee.first_name,
            employee.last_name,
            employee.photo_url,
        )
        for employee in Employee.query(Employee.terminated == False)  # noqa
    ]
    sql = 'insert into employee_search (username, first_name, last_name, photo_url) values (%s, %s, %s, %s);'
    with MySql().db.connect() as conn:
        conn.execute('Use employees;')
        conn.execute('truncate employee_search;')
        conn.execute(sql, employees)
