# -*- coding: utf-8 -*-
from time import mktime

from google.appengine.ext import ndb


class LoveLink(ndb.Model):
    """Models an instance of a Love Link."""
    hash_key = ndb.StringProperty()
    message = ndb.TextProperty()
    recipient_list = ndb.TextProperty()
    timestamp = ndb.DateTimeProperty(auto_now_add=True)

    @property
    def seconds_since_epoch(self):
        return int(mktime(self.timestamp.timetuple()))
