# -*- coding: utf-8 -*-
from datetime import datetime
from google.appengine.api import taskqueue

import config
import logic.alias
import logic.department
import logic.email
import logic.event

from errors import TaintedLove
from logic.toggle import get_toggle_state
from models import Employee
from models import Love
from models import LoveCount
from models.toggle import LOVE_SENDING_ENABLED
from util.render import render_template


def _love_query(start_dt, end_dt, include_secret):
    query = Love.query().order(-Love.timestamp)
    if type(start_dt) is datetime:
        query = query.filter(Love.timestamp >= start_dt)
    if type(end_dt) is datetime:
        query = query.filter(Love.timestamp <= end_dt)
    if type(include_secret) is bool and include_secret is False:
        query = query.filter(Love.secret == False)  # noqa
    return query


def _sent_love_query(employee_key, start_dt, end_dt, include_secret):
    return _love_query(start_dt, end_dt, include_secret).filter(Love.sender_key == employee_key)


def _received_love_query(employee_key, start_dt, end_dt, include_secret):
    return _love_query(start_dt, end_dt, include_secret).filter(Love.recipient_key == employee_key)


def recent_sent_love(employee_key, start_dt=None, end_dt=None, include_secret=True, limit=None):
    query = _sent_love_query(employee_key, start_dt, end_dt, include_secret)
    return query.fetch_async(limit) if type(limit) is int else query.fetch_async()


def recent_received_love(employee_key, start_dt=None, end_dt=None, include_secret=True, limit=None):
    query = _received_love_query(employee_key, start_dt, end_dt, include_secret)
    return query.fetch_async(limit) if type(limit) is int else query.fetch_async()


def send_love_email(l):
    """Send an email notifying the recipient of l about their love."""
    sender_future = l.sender_key.get_async()
    recipient_future = l.recipient_key.get_async()

    # Remove this love from recent_love if present (datastore is funny sometimes)
    recent_love = recent_received_love(l.recipient_key, limit=4).get_result()
    index_to_remove = None
    for i, love in enumerate(recent_love):
        if l.sender_key == love.sender_key and l.recipient_key == love.recipient_key and l.message == love.message:
            index_to_remove = i
            break
    if index_to_remove is not None:
        del recent_love[index_to_remove]

    sender = sender_future.get_result()
    recipient = recipient_future.get_result()

    from_ = config.LOVE_SENDER_EMAIL
    to = recipient.user.email()
    subject = u'Love from {}'.format(sender.full_name)

    body_text = u'"{}"\n\n{}'.format(
        l.message,
        '(Sent secretly)' if l.secret else ''
    )

    body_html = render_template(
        'email.html',
        love=l,
        sender=sender,
        recipient=recipient,
        recent_love_and_lovers=[(love, love.sender_key.get()) for love in recent_love[:3]]
    )

    logic.email.send_email(from_, to, subject, body_html, body_text)


def get_love(sender_username=None, recipient_username=None, limit=None):
    """Get all love from a particular sender or to a particular recipient.

    :param sender_username: If present, only return love sent from a particular user.
    :param recipient_username: If present, only return love sent to a particular user.
    :param limit: If present, only return this many items.
    """
    sender_username = logic.alias.name_for_alias(sender_username)
    recipient_username = logic.alias.name_for_alias(recipient_username)

    if not (sender_username or recipient_username):
        raise TaintedLove('Not gonna give you all the love in the world. Sorry.')

    if sender_username == recipient_username:
        raise TaintedLove('Who sends love to themselves? Honestly?')

    love_query = (
        Love.query()
        .filter(Love.secret == False)  # noqa
        .order(-Love.timestamp)
    )

    if sender_username:
        sender_key = Employee.get_key_for_username(sender_username)
        love_query = love_query.filter(Love.sender_key == sender_key)

    if recipient_username:
        recipient_key = Employee.get_key_for_username(recipient_username)
        love_query = love_query.filter(Love.recipient_key == recipient_key)

    if limit:
        return love_query.fetch_async(limit)
    else:
        return love_query.fetch_async()


def send_loves(recipients, message, sender_username=None, secret=False):
    if get_toggle_state(LOVE_SENDING_ENABLED) is False:
        raise TaintedLove('Sorry, sending love is temporarily disabled. Please try again in a few minutes.')

    if sender_username is None:
        sender_username = Employee.get_current_employee().username

    sender_username = logic.alias.name_for_alias(sender_username)
    sender_key = Employee.query(
            Employee.username == sender_username,
            Employee.terminated == False,
        ).get(keys_only=True)  # noqa

    if sender_key is None:
        raise TaintedLove(u'Sorry, {} is not a valid user.'.format(sender_username))

    unique_recipients = set([logic.alias.name_for_alias(name) for name in recipients])

    if len(recipients) != len(unique_recipients):
        raise TaintedLove(u'Sorry, you are trying to send love to a user multiple times.')

    # Only raise an error if the only recipient is the sender.
    if sender_username in unique_recipients:
        unique_recipients.remove(sender_username)
        if len(unique_recipients) == 0:
            raise TaintedLove(u'You can love yourself, but not on {}!'.format(
                config.APP_NAME
            ))

    # validate all recipients before carrying out any Love transactions
    recipient_keys = []
    for recipient_username in unique_recipients:
        recipient_key = Employee.query(
            Employee.username == recipient_username,
            Employee.terminated == False
        ).get(keys_only=True)  # noqa

        if recipient_key is None:
            raise TaintedLove(u'Sorry, {} is not a valid user.'.format(recipient_username))
        else:
            recipient_keys += [recipient_key]

    for recipient_key in recipient_keys:
        _send_love(recipient_key, message, sender_key, secret)

    return unique_recipients


def _send_love(recipient_key, message, sender_key, secret):
    """Send love and do associated bookkeeping."""
    new_love = Love(
        sender_key=sender_key,
        recipient_key=recipient_key,
        message=message,
        secret=(secret is True),
    )
    new_love.put()
    LoveCount.update(new_love)

    # Send email asynchronously
    taskqueue.add(
        url='/tasks/love/email',
        params={
            'id': new_love.key.id()
        }
    )

    if not secret:
        logic.event.add_event(
            logic.event.LOVESENT,
            {'love_id': new_love.key.id()},
        )
