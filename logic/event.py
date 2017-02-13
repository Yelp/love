# -*- coding: utf-8 -*-
import json

from google.appengine.api import taskqueue


LOVESENT = 'lovesent'

EVENTS = set([
    LOVESENT,
])


def add_event(event, options={}):
    payload = {
        'event': event,
        'options': options,
    }

    taskqueue.add(
        queue_name='events',
        url='/tasks/subscribers/notify',
        headers={'Content-Type': 'application/json'},
        payload=json.dumps(payload),
    )
