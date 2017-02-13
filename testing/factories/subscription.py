# -*- coding: utf-8 -*-
from models import Subscription


def create_subscription(
    request_url='johndoe',
    active=False,
    event='lovesent',
    secret='secret',
):
    return Subscription.create_from_dict({
        'request_url': request_url,
        'active': active,
        'event': event,
        'secret': secret,
    })
