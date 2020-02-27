# -*- coding: utf-8 -*-
import csv
import json
import os.path
import logging

# from google.appengine.api import search
# from google.appengine.api.runtime import memory_usage
from google.cloud import ndb

import config
from errors import NoSuchEmployee

# from logic import chunk
from logic.secret import get_secret
from logic.toggle import set_toggle_state
from models import Employee
from models import Love
from models import LoveCount
from models.toggle import LOVE_SENDING_ENABLED


INDEX_NAME = "employees"


def csv_import_file():
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "../import/employees.csv"
    )


def load_employees_from_csv():
    employee_dicts = _get_employee_info_from_csv()
    set_toggle_state(LOVE_SENDING_ENABLED, False)
    _update_employees(employee_dicts)
    set_toggle_state(LOVE_SENDING_ENABLED, True)
    # rebuild_index()


def _get_employee_info_from_csv():
    logging.info("Reading employees from csv file...")
    employees = csv.DictReader(open(csv_import_file()))
    logging.info("Done reading employees from csv file.")
    return employees


def _get_employee_info_from_s3():
    from boto import connect_s3
    from boto.s3.key import Key

    logging.info("Reading employees file from S3...")
    key = Key(
        connect_s3(
            aws_access_key_id=get_secret("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=get_secret("AWS_SECRET_ACCESS_KEY"),
        ).get_bucket(config.S3_BUCKET),
        "employees.json",
    )
    employee_dicts = json.loads(key.get_contents_as_string())
    logging.info("Done reading employees file from S3.")
    return employee_dicts


def _update_employees(employee_dicts):
    """Given a JSON string in the format "[{employee info 1}, {employee info 2}, ...]",
    create new employee records and update existing records as necessary.

    Then determine whether any employees have been terminated since the last update,
    and mark these employees as such.
    """
    logging.info("Updating employees...")

    db_employee_dict = {employee.username: employee for employee in Employee.query()}

    all_employees, new_employees = [], []
    current_usernames = set()
    for d in employee_dicts[:25]:  # TODO undo this slice
        existing_employee = db_employee_dict.get(d["username"])
        if existing_employee is None:
            new_employee = Employee.create_from_dict(d, persist=False)
            all_employees.append(new_employee)
            new_employees.append(new_employee)
        else:
            existing_employee.update_from_dict(d)
            # If the user is in the S3 dump, then the user is no longer
            # terminated.
            existing_employee.terminated = False
            all_employees.append(existing_employee)

        current_usernames.add(d["username"])
        # if len(all_employees) % 200 == 0:
        logging.info(f"Processed {len(all_employees)} employees")
    ndb.put_multi(all_employees)

    # Figure out if there are any employees in the DB that aren't in the S3
    # dump. These are terminated employees, and we need to mark them as such.
    db_usernames = set(db_employee_dict.keys())

    terminated_usernames = db_usernames - current_usernames
    terminated_employees = []
    for username in terminated_usernames:
        employee = db_employee_dict[username]
        employee.terminated = True
        terminated_employees.append(employee)
    ndb.put_multi(terminated_employees)

    logging.info("Done updating employees.")


def combine_employees(old_username, new_username):
    set_toggle_state(LOVE_SENDING_ENABLED, False)

    old_employee_key = Employee.query(Employee.username == old_username).get(
        keys_only=True
    )
    new_employee_key = Employee.query(Employee.username == new_username).get(
        keys_only=True
    )
    if not old_employee_key:
        raise NoSuchEmployee(old_username)
    elif not new_employee_key:
        raise NoSuchEmployee(new_username)

    # First, we need to update the actual instances of Love sent to/from the old employee
    logging.info(f"Reassigning {old_username}'s love to {new_username}...")

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
    logging.info("Done reassigning love.")

    # Second, we need to update the LoveCount table
    logging.info("Updating LoveCount table...")

    love_counts_to_delete, love_counts_to_save = [], []

    for old_love_count in LoveCount.query(ancestor=old_employee_key).iter():
        # Try to find a corresponding row for the new employee
        new_love_count = LoveCount.query(
            ancestor=new_employee_key,
            filters=(LoveCount.week_start == old_love_count.week_start),
        ).get()

        if new_love_count is None:
            # If there's no corresponding row for the new user, create one
            new_love_count = LoveCount(
                parent=new_employee_key,
                received_count=old_love_count.received_count,
                sent_count=old_love_count.sent_count,
                week_start=old_love_count.week_start,
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
    logging.info("Done updating LoveCount table.")

    # Now we can delete the old employee
    logging.info(f"Deleting employee {old_username}...")
    old_employee_key.delete()
    logging.info("Done deleting employee.")

    # ... Which means we need to rebuild the index
    # rebuild_index()

    set_toggle_state(LOVE_SENDING_ENABLED, True)


def employees_matching_prefix(prefix):
    """Returns a list of (full name, username) tuples for users that match the given prefix."""
    if not prefix:
        return []

    user_tuples = set()
    results = Employee.query().filter(Employee.username >= prefix).fetch(limit=15)
    # search_query = search.Query(
    #     query_string=prefix,
    #     options=search.QueryOptions(
    #         limit=15))
    # results = search.Index(name=INDEX_NAME).search(search_query)
    for r in results:
        username, full_name = None, None
        full_name = r.full_name
        username = r.username
        if username is not None and full_name is not None:
            photo_url = r.photo_url
            user_tuples.add((full_name, username, photo_url))

    user_tuples = list(user_tuples)
    user_tuples.sort()
    return user_tuples


def load_employees():
    employee_dicts = _get_employee_info_from_s3()
    set_toggle_state(LOVE_SENDING_ENABLED, False)
    _update_employees(employee_dicts)
    set_toggle_state(LOVE_SENDING_ENABLED, True)
    # rebuild_index()


# def rebuild_index():
#     active_employees_future = Employee.query(
#         Employee.terminated == False
#     ).fetch_async()  # noqa
#     _clear_index()
#     _index_employees(active_employees_future.get_result())
