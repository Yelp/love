# -*- coding: utf-8 -*-
import config
import requests
import base64
import requests_toolbelt.adapters.appengine
from logic.secret import get_secret

requests_toolbelt.adapters.appengine.monkeypatch()


def get_employees():
    response = requests.get(
        '{}/employees'.format(config.CORPAPI_BASE_URL),
        headers={
            'X-API-Key': get_secret('API_KEY'),
        },
    ).json()
    return response


def get_employee_photo(alias):
    try:
        response = requests.get(
            '{}/photos/{}'.format(config.CORPAPI_BASE_URL, alias),
            headers={
                'X-API-Key': get_secret('API_KEY'),
            },
        ).json().get('imagebase64')

        return base64.decodestring(response) if response else None
    except Exception:
        # Sometimes the endpoint is overloaded but no problem
        # the data will be fetch the next run
        return None
