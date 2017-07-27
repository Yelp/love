# -*- coding: utf-8 -*-

from google.appengine.ext import ndb

from errors import NoSuchLoveLink
from models import LoveLink


def get_love_link(hash_key):
    loveLink = LoveLink.query(LoveLink.hash_key == hash_key).get()
    if (loveLink is None):
        raise NoSuchLoveLink("Couldn't Love Link with id {}".format(hash_key))
    return loveLink
