# -*- coding: utf-8 -*-
from google.cloud import ndb


class Secret(ndb.Model):
    value = ndb.StringProperty()
