# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import timedelta

import loveapp.logic.love_count
from loveapp.logic import TIMESPAN_LAST_WEEK
from loveapp.logic import to_the_future
from loveapp.logic import utc_week_limits


def get_leaderboard_data(timespan, department, office=None):
    # If last week, we need to subtract *before* getting the week limits to
    # avoid being off by one hour on weeks that include a DST transition
    utc_now = datetime.utcnow()
    if timespan == TIMESPAN_LAST_WEEK:
        utc_now -= timedelta(days=7)
    utc_week_start, _ = utc_week_limits(utc_now)

    top_lovers, top_lovees = loveapp.logic.love_count.top_lovers_and_lovees(
        utc_week_start,
        dept=department,
        office=office,
    )

    top_lover_dicts = [
        {
            'employee': employee_key.get_async(),
            'num_sent': sent_count
        }
        for employee_key, sent_count
        in top_lovers
    ]

    top_loved_dicts = [
        {
            'employee': employee_key.get_async(),
            'num_received': received_count
        }
        for employee_key, received_count
        in top_lovees
    ]

    # get results for the futures set up previously
    list(map(to_the_future, top_lover_dicts))
    list(map(to_the_future, top_loved_dicts))
    return (top_lover_dicts, top_loved_dicts)
