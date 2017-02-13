# -*- coding: utf-8 -*-
from google.appengine.ext import ndb

from logic.notification_request import CONTENT_TYPE_JSON
from models import Employee


class Subscription(ndb.Model):
    """Models a webhook subscription."""
    request_method = ndb.StringProperty(required=True, default='post')
    request_format = ndb.StringProperty(required=True, default=CONTENT_TYPE_JSON)
    request_url = ndb.StringProperty(required=True)
    active = ndb.BooleanProperty(required=True, default=False)
    event = ndb.StringProperty(required=True)
    secret = ndb.StringProperty(required=True)
    timestamp = ndb.DateTimeProperty(auto_now_add=True)
    owner_key = ndb.KeyProperty(kind=Employee)

    @classmethod
    def create_from_dict(cls, d, persist=True):
        new_subscription = cls()
        new_subscription.owner_key = Employee.get_current_employee().key
        new_subscription.request_url = d['request_url']
        new_subscription.active = d['active']
        new_subscription.event = d['event']
        new_subscription.secret = d['secret']

        if persist is True:
            new_subscription.put()

        return new_subscription

    @classmethod
    def all_active_for_event(cls, event):
        return cls.query(
            cls.active == True,  # noqa
            cls.event == event,
        )
