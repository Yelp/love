# -*- coding: utf-8 -*-
import csv
import json
import os.path
import logging

from boto import connect_s3
from boto.s3.key import Key
from google.appengine.api import search
from google.appengine.ext import ndb

import config
from errors import NoSuchEmployee
from logic.secret import get_secret
from logic.toggle import set_toggle_state
from models import Employee
from models import Love
from models import LoveCount
from models.toggle import LOVE_SENDING_ENABLED


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


def direct_load_employee(d):
    _update_employees([d])


def _get_employee_info_from_csv():
    logging.info('Reading employees from csv file...')
    employees = csv.DictReader(open(csv_import_file()))
    logging.info('Done.')
    return employees


def _clear_index():
    logging.info('Clearing index...')
    index = search.Index(name=INDEX_NAME)
    index_delete_futures = []
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
        index_delete_futures.append(index.delete_async(doc_ids))
    for index_delete_future in index_delete_futures:
        index_delete_future.get_result()
    logging.info('Done.')


def _generate_substrings(string):
    """Given a string, return a string of all its substrings (not including the original)
    anchored at the first character, concatenated with spaces.

    Example:
        _concatenate_substrings('arothman') => 'a ar aro arot aroth arothm arothma'
    """
    return ' '.join([string[:i] for i in xrange(1, len(string))])


def _get_employee_info_from_s3():
    logging.info('Reading employees file from S3...')
    key = Key(
        connect_s3(
            aws_access_key_id=get_secret('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=get_secret('AWS_SECRET_ACCESS_KEY'),
        ).get_bucket(config.S3_BUCKET),
        'employees.json',
    )
    employee_dicts = json.loads(key.get_contents_as_string())
    logging.info('Done.')
    return employee_dicts


def paged_employees(page_size):
    """
    Iterate over employees in chunks of page_size. But instead of simply chunking them in
    memory, the query actually returns page_size amount each time.
    """
    cursor = None
    query = Employee.query(Employee.terminated == False)  # noqa
    (results, cursor, more) = query.fetch_page(page_size)

    while True:
        # an empty list means no more results
        if not results:
            return

        # queue up the next page asynchronously
        future = query.fetch_page_async(page_size, start_cursor=cursor)

        yield results

        # when more is False, no more results are available
        if not more:
            return

        # get the next page from the future
        (results, cursor, more) = future.get_result()


def _index_employees():
    logging.info('Indexing employees...')
    index = search.Index(name=INDEX_NAME)
    # According to appengine, put can handle a maximum of 200 documents,
    # and apparently batching is more efficient
    for chunk_of_200 in paged_employees(200):
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
                    search.TextField(name='username', value=unicode(employee.username)),
                    search.TextField(name='substrings', value=substrings),
                ])
                documents.append(doc)
        results = index.put_async(documents).get_result()
        del results
        del chunk_of_200
        del documents
        logging.info('Chunk!')
    logging.info('Done.')


def _update_employees(employee_dicts):
    """Given a JSON string in the format "[{employee info 1}, {employee info 2}, ...]",
    create new employee records and update existing records as necessary.

    Then determine whether any employees have been terminated since the last update,
    and mark these employees as such.
    """
    logging.info('Updating employees...')

    employees = []
    for d in employee_dicts:
        existing_employee = Employee.query(Employee.username == d['username']).get()
        if existing_employee is None:
            new_employee = Employee.create_from_dict(d, persist=False)
            employees.append(new_employee)
        else:
            existing_employee.update_from_dict(d)
            # If the user is in the S3 dump, then the user is no longer
            # terminated.
            existing_employee.terminated = False
            employees.append(existing_employee)

        # write to db every 500 employees so we save memory
        if len(employees) == 500:
            ndb.put_multi(employees)
            del employees
            employees = []

    if employees:
        ndb.put_multi(employees)

    logging.info('Done.')


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
    logging.info('Done.')

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
    logging.info('Done.')

    # Now we can delete the old employee
    logging.info('Deleting employee {}...'.format(old_username))
    old_employee_key.delete()
    logging.info('Done.')

    # ... Which means we need to rebuild the index
    rebuild_index()

    set_toggle_state(LOVE_SENDING_ENABLED, True)


def employees_matching_prefix(prefix):
    """Returns a list of (full name, username) tuples for users that match the given prefix."""
    if not prefix:
        return []

    user_tuples = set()

    results = search.Index(name=INDEX_NAME).search(prefix)
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
            user_tuples.add((full_name, username))

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
    _clear_index()
    _index_employees()
