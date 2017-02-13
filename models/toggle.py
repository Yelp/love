# -*- coding: utf-8 -*-
from google.appengine.ext import ndb


LOVE_SENDING_ENABLED = 'love_sending_enabled'
TOGGLE_NAMES = set([
    LOVE_SENDING_ENABLED
])

TOGGLE_STATES = set([True, False])


class Toggle(ndb.Model):
    name = ndb.StringProperty()
    state = ndb.BooleanProperty()
