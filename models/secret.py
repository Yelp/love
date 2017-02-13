# -*- coding: utf-8 -*-
from google.appengine.ext import ndb


class Secret(ndb.Model):
    value = ndb.StringProperty()
