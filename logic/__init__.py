# -*- coding: utf-8 -*-
from datetime import timedelta
from itertools import zip_longest

import pytz
from google.appengine.ext import ndb


TIMESPAN_LAST_WEEK = 'last_week'
TIMESPAN_THIS_WEEK = 'this_week'


def chunk(iterable, chunk_size):
    """Collect data into fixed-length chunks or blocks (http://docs.python.org/2/library/itertools.html#recipes)"""
    args = [iter(iterable)] * chunk_size
    return zip_longest(*args)


def to_the_future(dict):
    for k, v in dict.iteritems():
        if issubclass(v.__class__, ndb.Future):
            dict[k] = v.get_result()


def utc_week_limits(utc_dt):
    """Returns US/Pacific start (12:00 am Sunday) and end (11:59 pm Saturday) of the week containing utc_dt, in UTC."""
    local_now = utc_dt.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Pacific'))

    local_week_start = local_now - timedelta(
        days=local_now.weekday() + 1,
        hours=local_now.hour,
        minutes=local_now.minute,
        seconds=local_now.second,
        microseconds=local_now.microsecond,
    )
    local_week_end = local_week_start + timedelta(days=7, minutes=-1)

    utc_week_start = local_week_start.astimezone(pytz.utc).replace(tzinfo=None)
    utc_week_end = local_week_end.astimezone(pytz.utc).replace(tzinfo=None)

    return (utc_week_start, utc_week_end)
