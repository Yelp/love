# -*- coding: utf-8 -*-
from time import mktime

from google.appengine.ext import ndb

from loveapp.models import Employee


class Love(ndb.Model):
    """Models an instance of sent love."""
    message = ndb.TextProperty()
    recipient_key = ndb.KeyProperty(kind=Employee)
    secret = ndb.BooleanProperty(default=False)
    sender_key = ndb.KeyProperty(kind=Employee)
    timestamp = ndb.DateTimeProperty(auto_now_add=True)
    company_values = ndb.StringProperty(repeated=True)

    @property
    def seconds_since_epoch(self):
        return int(mktime(self.timestamp.timetuple()))
