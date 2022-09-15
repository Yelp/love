# -*- coding: utf-8 -*-
import datetime
import logging
from collections import OrderedDict

from google.appengine.api.runtime import memory_usage
from google.appengine.ext import ndb

from logic import utc_week_limits
from logic.toggle import set_toggle_state
from models import Employee
from models import Love
from models import LoveCount
from models.toggle import LOVE_SENDING_ENABLED


def top_lovers_and_lovees(utc_week_start, dept=None, office=None, limit=20):
    """Synchronously return a list of (employee key, sent love count) and a list of
    (employee key, received love count), each sorted in descending order of love sent
    or received.
    """
    sent_query = LoveCount.query(LoveCount.week_start == utc_week_start)
    if dept:
        sent_query = sent_query.filter(LoveCount.department == dept)

    if office:
        sent_query = sent_query.filter(LoveCount.office == office)

    sent = sent_query.order(-LoveCount.sent_count).fetch()
    lovers = []
    for c in sent:
        if len(lovers) == limit:
            break
        if c.sent_count == 0:
            continue
        employee_key = c.key.parent()

        lovers.append((employee_key, c.sent_count))

    received = sorted(sent, key=lambda c: c.received_count, reverse=True)
    lovees = []
    for c in received:
        if len(lovees) == limit:
            break
        if c.received_count == 0:
            continue
        employee_key = c.key.parent()

        lovees.append((employee_key, c.received_count))

    return (lovers, lovees)


def rebuild_love_count():
    utc_dt = datetime.datetime.utcnow() - datetime.timedelta(days=7)  # rebuild last week and this week
    week_start, _ = utc_week_limits(utc_dt)

    set_toggle_state(LOVE_SENDING_ENABLED, False)

    logging.info('Deleting LoveCount table... {}MB'.format(memory_usage().current()))
    ndb.delete_multi(LoveCount.query(LoveCount.week_start >= week_start).fetch(keys_only=True))
    employee_dict = {
        employee.key: employee
        for employee in Employee.query()
    }
    logging.info('Rebuilding LoveCount table... {}MB'.format(memory_usage().current()))
    cursor = None
    count = 0
    while True:
        loves, cursor, has_more = Love.query(Love.timestamp >= week_start).fetch_page(500, start_cursor=cursor)
        for love in loves:
            LoveCount.update(love, employee_dict=employee_dict)
        count += len(loves)
        logging.info('Processed {} loves, {}MB'.format(count, memory_usage().current()))
        if not has_more:
            break
    logging.info('Done. {}MB'.format(memory_usage().current()))

    set_toggle_state(LOVE_SENDING_ENABLED, True)


def get_love_counts_by_week(username, start_date=None, end_date=None):
    """Return the amount of love sent and received by a particular employee, broken down by week."""

    employee_key = Employee.get_key_for_username(username)
    received_by_week, sent_by_week = OrderedDict(), OrderedDict()

    love_count_query = LoveCount.query(ancestor=employee_key)
    if start_date:
        love_count_query = love_count_query.filter(LoveCount.week_start >= start_date)

    if end_date:
        love_count_query = love_count_query.filter(LoveCount.week_start <= end_date)

    for love_count in love_count_query.order(-LoveCount.week_start).iter():
        received_by_week[love_count.week_start] = love_count.received_count
        sent_by_week[love_count.week_start] = love_count.sent_count

    return received_by_week, sent_by_week
