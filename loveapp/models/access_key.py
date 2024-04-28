# -*- coding: utf-8 -*-
from uuid import uuid4

from google.appengine.ext import ndb


class AccessKey(ndb.Model):
    """Models an instance of an API key."""
    access_key = ndb.StringProperty()
    description = ndb.TextProperty()

    @staticmethod
    def generate_uuid():
        return uuid4().hex

    @classmethod
    def create(cls, description):
        new_key = cls()
        new_key.access_key = cls.generate_uuid()
        new_key.description = description
        new_key.put()

        return new_key
