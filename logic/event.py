# -*- coding: utf-8 -*-
from models.tasks import Tasks


LOVESENT = 'lovesent'

EVENTS = set([
    LOVESENT,
])


def add_event(event, relative_uri, options={}, http_method='POST'):
    if options:
        payload = {
            'event': event,
            'options': options,
        }
    else:
        payload = {}
    task = {
        'app_engine_http_request': {  # Specify the type of request.
            'http_method': http_method,
            'relative_uri': relative_uri,
        }
    }
    Tasks('events').create_task(payload, task)
