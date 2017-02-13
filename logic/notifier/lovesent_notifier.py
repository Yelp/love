# -*- coding: utf-8 -*-
from google.appengine.ext import ndb

import logic.event

from logic.notification_request import NotificationRequest
from models.love import Love
from models.subscription import Subscription


class LovesentNotifier(object):

    event = logic.event.LOVESENT

    def __init__(self, *args, **kwargs):
        self.love = ndb.Key(Love, kwargs.get('love_id')).get()

    def notify(self):
        subscriptions = self._subscriptions()
        for subscription in subscriptions:
            NotificationRequest(subscription, self.payload()).send()
        return len(subscriptions)

    def payload(self):
        sender = self.love.sender_key.get()
        receiver = self.love.recipient_key.get()
        return {
            'sender': {
                'full_name': sender.full_name,
                'username': sender.username,
                'email': sender.user.email(),
            },
            'receiver': {
                'full_name': receiver.full_name,
                'username': receiver.username,
                'email': receiver.user.email(),
            },
            'message': self.love.message,
            'timestamp': self.love.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _subscriptions(self):
        return Subscription.all_active_for_event(self.event).fetch()
