# -*- coding: utf-8 -*-
import logging

from google.appengine.ext import ndb

from logic.toggle import set_toggle_state
from models import Love
from models import LoveCount
from models.toggle import LOVE_SENDING_ENABLED


def top_lovers_and_lovees(utc_week_start, dept=None, office=None, limit=20):
    """Synchronously return a list of (employee key, sent love count) and a list of
    (employee key, received love count), each sorted in descending order of love sent
    or received.
    """
    sent = LoveCount.query(LoveCount.week_start == utc_week_start).order(-LoveCount.sent_count).fetch()
    lovers = []
    for c in sent:
        if len(lovers) == limit:
            break
        if c.sent_count == 0:
            continue
        employee_key = c.key.parent()
        employee = employee_key.get()
        employee.office = employee.office or ''
        if (
            not dept or (employee.meta_department == dept or employee.department == dept)
        ) and (
            not office or employee.office.replace(':', '').startswith(office)
        ):
            lovers.append((employee_key, c.sent_count))
    received = sorted(sent, key=lambda c: c.received_count, reverse=True)
    lovees = []
    for c in received:
        if len(lovees) == limit:
            break
        if c.received_count == 0:
            continue
        employee_key = c.key.parent()
        employee = employee_key.get()
        employee.office = employee.office or ''
        if (
            not dept or (employee.meta_department == dept or employee.department == dept)
        ) and (
            not office or employee.office.replace(':', '').startswith(office)
        ):
            lovees.append((employee_key, c.received_count))

    return (lovers, lovees)


def rebuild_love_count():
    set_toggle_state(LOVE_SENDING_ENABLED, False)

    logging.info('Rebuilding LoveCount table...')
    ndb.delete_multi(LoveCount.query().fetch(keys_only=True))
    for l in Love.query().iter(batch_size=1000):
        LoveCount.update(l)
    logging.info('Done.')

    set_toggle_state(LOVE_SENDING_ENABLED, True)
