# -*- coding: utf-8 -*-
from google.cloud import ndb

from models.employee import Employee


class Alias(ndb.Model):
    """Models an instance of an alias."""

    name = ndb.StringProperty(required=True)
    owner_key = ndb.KeyProperty(kind=Employee)
    timestamp = ndb.DateTimeProperty(auto_now_add=True)
