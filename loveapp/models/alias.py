# -*- coding: utf-8 -*-
from google.appengine.ext import ndb

from loveapp.models.employee import Employee


class Alias(ndb.Model):
    """Models an instance of an alias."""
    name = ndb.StringProperty(required=True)
    owner_key = ndb.KeyProperty(kind=Employee)
    timestamp = ndb.DateTimeProperty(auto_now_add=True)
