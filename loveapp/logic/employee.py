# -*- coding: utf-8 -*-
import csv
import json
import logging
import os.path

import boto3
from google.appengine.api import search
from google.appengine.api.runtime import memory_usage
from google.appengine.ext import ndb

import loveapp.config as config
from errors import NoSuchEmployee
from loveapp.logic import chunk
from loveapp.logic.office import OfficeParser
from loveapp.logic.secret import get_secret
from loveapp.logic.toggle import set_toggle_state
from loveapp.models import Employee
from loveapp.models import Love
from loveapp.models import LoveCount
from loveapp.models.toggle import LOVE_SENDING_ENABLED


INDEX_NAME = 'employees'


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
    rebuild_index()


def _get_employee_info_from_csv():
    logging.info('Reading employees from csv file...')
    employees = csv.DictReader(open(csv_import_file()))
    logging.info('Done reading employees from csv file.')
    return employees


def _clear_index():
    logging.info('Clearing index... {}MB'.format(memory_usage().current))
    index = search.Index(name=INDEX_NAME)
    last_id = None
    while True:
        # We can batch up to 200 doc_ids in the delete call, and
        # batching is better according to the docs. Because we're deleting
        # async, we need to keep track of where we left off each time
        # we do get_range
        use_start_object = False
        if last_id is None:
            use_start_object = True
        doc_ids = [
            doc.doc_id for doc in index.get_range(
                ids_only=True,
                limit=200,
                start_id=last_id,
                include_start_object=use_start_object,
            )
        ]
        if not doc_ids:
            break
        last_id = doc_ids[-1]
        index.delete(doc_ids)

    logging.info('Done clearing index. {}MB'.format(memory_usage().current))


def _generate_substrings(string):
    """Given a string, return a string of all its substrings (not including the original)
    anchored at the first character, concatenated with spaces.

    Example:
        _concatenate_substrings('arothman') => 'a ar aro arot aroth arothm arothma'
    """
    return ' '.join([string[:i] for i in range(1, len(string))])


def _get_employee_info_from_s3():
    logging.info('Reading employees file from S3... {}MB'.format(memory_usage().current))
    session = boto3.Session(
        aws_access_key_id=get_secret('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=get_secret('AWS_SECRET_ACCESS_KEY'),
    )
    s3 = session.resource('s3')
    bucket = s3.Bucket(config.S3_BUCKET)
    obj = bucket.Object('employees_appeng.json')
    employee_dicts = json.loads(obj.get()['Body'].read().decode('utf-8'))   
    logging.info('Done reading employees file from S3. {}MB'.format(memory_usage().current))
    return employee_dicts


def _index_employees(employees):
    logging.info('Indexing employees... {}MB'.format(memory_usage().current))
    index = search.Index(name=INDEX_NAME)
    # According to appengine, put can handle a maximum of 200 documents,
    # and apparently batching is more efficient
    for chunk_of_200 in chunk(employees, 200):
        documents = []
        for employee in chunk_of_200:
            if employee is not None:
                # Gross hack to support prefix matching, see documentation for _generate_substrings
                substrings = u' '.join([
                    _generate_substrings(employee.first_name),
                    _generate_substrings(employee.last_name),
                    _generate_substrings(employee.username),
                ])
                doc = search.Document(fields=[
                    # Full name is already unicode
                    search.TextField(name='full_name', value=employee.full_name),
                    search.TextField(name='username', value=employee.username),
                    search.TextField(name='substrings', value=substrings),
                ])
                documents.append(doc)
        index.put(documents)
    logging.info('Done indexing employees. {}MB'.format(memory_usage().current))


def _update_employees(employee_dicts):
    """Given a JSON string in the format "[{employee info 1}, {employee info 2}, ...]",
    create new employee records and update existing records as necessary.

    Then determine whether any employees have been terminated since the last update,
    and mark these employees as such.
    """
    employee_dicts = list(employee_dicts)

    logging.info('Updating employees... {}MB'.format(memory_usage().current))

    db_employee_dict = {
        employee.username: employee
        for employee in Employee.query()
    }

    all_employees, new_employees = [], []
    current_usernames = set()
    office_parser = OfficeParser(employee_dicts)

    for d in employee_dicts:
        d['office'] = office_parser.get_office_name(
            employee_office_location=d['office'],
            employee_department=d.get('department'),
        ) if d.get('office') else None
        existing_employee = db_employee_dict.get(d['username'])

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

        current_usernames.add(d['username'])
        if len(all_employees) % 200 == 0:
            logging.info('Processed {} employees, {}MB'.format(len(all_employees), memory_usage().current))
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

    logging.info('Done updating employees. {}MB'.format(memory_usage().current))


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
            ancestor=new_employee_key,
            filters=(LoveCount.week_start == old_love_count.week_start)
        ).get()

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

    # ... Which means we need to rebuild the index
    rebuild_index()

    set_toggle_state(LOVE_SENDING_ENABLED, True)


def employees_matching_prefix(prefix):
    """Returns a list of (full name, username) tuples for users that match the given prefix."""
    if not prefix:
        return []

    user_tuples = set()

    search_query = search.Query(
        query_string=prefix,
        options=search.QueryOptions(
            limit=15))
    results = search.Index(name=INDEX_NAME).search(search_query)
    for r in results:
        username, full_name = None, None
        for f in r.fields:
            if f.name == 'full_name':
                full_name = f.value
            elif f.name == 'username':
                username = f.value
            else:
                continue
        if username is not None and full_name is not None:
            photo_url = Employee.query(Employee.username == username).get().get_photo_url()
            user_tuples.add((full_name, username, photo_url))

    user_tuples = list(user_tuples)
    user_tuples.sort()
    return user_tuples


def load_employees():
    employee_dicts = _get_employee_info_from_s3()
    set_toggle_state(LOVE_SENDING_ENABLED, False)
    _update_employees(employee_dicts)
    set_toggle_state(LOVE_SENDING_ENABLED, True)
    rebuild_index()


def rebuild_index():
    active_employees_future = Employee.query(Employee.terminated == False).fetch_async()  # noqa
    _clear_index()
    _index_employees(active_employees_future.get_result())
