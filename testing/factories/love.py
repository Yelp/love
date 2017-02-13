# -*- coding: utf-8 -*-
from models import Love

DEFAULT_LOVE_MESSAGE = 'So Long, and Thanks For All the Fish'


def create_love(
    sender_key,
    recipient_key,
    message=DEFAULT_LOVE_MESSAGE,
    secret=False,
):

    love = Love(
        sender_key=sender_key,
        recipient_key=recipient_key,
        message=message,
        secret=secret,
    )
    love.put()

    return love
