# -*- coding: utf-8 -*-
import datetime
import logging
import random
import string

import logic.alias
from errors import NoSuchLoveLink
from models import LoveLink
from models import Employee

from google.cloud import ndb


def get_love_link(hash_key):
    loveLink = LoveLink.query(LoveLink.hash_key == hash_key).get()
    if (loveLink is None):
        raise NoSuchLoveLink("Couldn't Love Link with id {}".format(hash_key))
    return loveLink


def generate_link_id():
    link_id = ''.join(random.choice(string.ascii_letters) for _ in range(5))
    return link_id


def create_love_link(recipients, message):
    logging.info('Creating love link')
    link_id = generate_link_id()
    new_love_link = LoveLink(
        hash_key=link_id,
        recipient_list=recipients,
        message=message,
    )
    logging.info(new_love_link)
    new_love_link.put()

    return new_love_link


def add_recipient(hash_key, recipient):
    loveLink = LoveLink.query(LoveLink.hash_key == hash_key).get()
    if (loveLink is None):
        raise NoSuchLoveLink("Couldn't Love Link with id {}".format(hash_key))

    # check that user exists, get_key_for_username throws an exception if not
    recipient_username = logic.alias.name_for_alias(recipient)
    Employee.get_key_for_username(recipient_username)

    loveLink.recipient_list += ', ' + recipient
    loveLink.put()


def love_links_cleanup():
    """
    Deletes love links that are more than a month (30 days) old.
    """
    earliest = datetime.datetime.now() - datetime.timedelta(days=30)
    love_links_keys = LoveLink.query(LoveLink.timestamp <= earliest).fetch(keys_only=True)
    logging.info('Preparing to delete love links older than {}.'.format(str(earliest)))
    ndb.delete_multi(love_links_keys)
    logging.info('Love links older than {} were deleted.'.format(str(earliest)))

    return
