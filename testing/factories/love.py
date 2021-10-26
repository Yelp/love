# -*- coding: utf-8 -*-
from models import Love

DEFAULT_LOVE_MESSAGE = 'So Long, and Thanks For All the Fish'


def create_love(
    sender_key,
    recipient_key,
    message=DEFAULT_LOVE_MESSAGE,
    secret=False,
    company_values=()
):

    love = Love(
        sender_key=sender_key,
        recipient_key=recipient_key,
        message=message,
        secret=secret,
        company_values=company_values
    )
    love.put()

    return love
