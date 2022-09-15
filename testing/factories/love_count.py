# -*- coding: utf-8 -*-
from datetime import datetime

from logic import utc_week_limits
from models import LoveCount


def create_love_count(
    parent_key,
    sent_count=10,
    received_count=50,
    week_start=None
):
    utc_week_start, _ = utc_week_limits(datetime.utcnow())

    lc = LoveCount(
        parent=parent_key,
        sent_count=sent_count,
        received_count=received_count,
        week_start=utc_week_start if week_start is None else week_start
    )
    lc.put()

    return lc
