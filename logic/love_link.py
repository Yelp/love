# -*- coding: utf-8 -*-
import logging
import random
import string

from errors import NoSuchLoveLink
from models import LoveLink


def get_love_link(hash_key):
    loveLink = LoveLink.query(LoveLink.hash_key == hash_key).get()
    if (loveLink is None):
        raise NoSuchLoveLink("Couldn't Love Link with id {}".format(hash_key))
    return loveLink


def create_love_link(recipients, message):
    logging.info('Creating love link')
    hash_key = ''.join(random.choice(string.lowercase) for x in range(10))
    new_love_link = LoveLink(
        hash_key=hash_key,
        recipient_list=recipients,
        message=message,
    )
    logging.info(new_love_link)
    new_love_link.put()

    return hash_key
