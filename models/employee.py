# -*- coding: utf-8 -*-
import base64
import hashlib
import functools

from google.appengine.ext import ndb
from google.appengine.api import users

import config
from errors import NoSuchEmployee
from logic.department import get_meta_department
from util.pagination import Pagination


def memoized(func):
    results = {}

    @functools.wraps(func)
    def _memoization_wrapper(*args):
        if args not in results:
            results[args] = func(*args)
        return results[args]

    def _forget_results():
        results.clear()

    _memoization_wrapper.forget_results = _forget_results
    return _memoization_wrapper


class Employee(ndb.Model, Pagination):
    """Models an Employee."""
    department = ndb.StringProperty(indexed=False)
    first_name = ndb.StringProperty(indexed=False)
    last_name = ndb.StringProperty(indexed=False)
    meta_department = ndb.StringProperty()
    photo_url = ndb.TextProperty()
    terminated = ndb.BooleanProperty(default=False)
    timestamp = ndb.DateTimeProperty(auto_now_add=True)
    user = ndb.UserProperty()
    username = ndb.StringProperty()

    @classmethod
    def get_current_employee(cls):
        user = users.get_current_user()
        user_email = user.email()
        employee = cls.query(cls.user == user, cls.terminated == False).get()  # noqa
        if employee is None:
            raise NoSuchEmployee('Couldn\'t find a Google Apps user with email {}'.format(user_email))
        return employee

    @classmethod
    def create_from_dict(cls, d, persist=True):
        new_employee = cls()
        new_employee.username = d['username']
        new_employee.user = users.User('{user}@{domain}'.format(user=new_employee.username, domain=config.DOMAIN))
        new_employee.update_from_dict(d)

        if persist is True:
            new_employee.put()

        return new_employee

    @classmethod
    def key_to_username(cls, key):
        return cls.query(cls.key == key).get().username

    @classmethod
    @memoized
    def get_key_for_username(cls, username):
        key = cls.query(cls.username == username, cls.terminated == False).get(keys_only=True)  # noqa
        if key is None:
            raise NoSuchEmployee("Couldn't find a Google Apps user with username {}".format(username))
        return key

    def update_from_dict(self, d):
        self.first_name = d['first_name']
        self.last_name = d['last_name']
        self.photo_url = d.get('photo_url')
        self.department = d.get('department')
        self.meta_department = get_meta_department(self.department)

    def get_gravatar(self):
        """Creates gravatar URL from email address."""
        email = '{user}@{domain}'.format(user=self.username, domain=config.DOMAIN)
        m = hashlib.md5()
        m.update(email)
        encoded_hash = base64.b16encode(m.digest()).lower()
        return '//gravatar.com/avatar/{}?s=200'.format(encoded_hash)

    def get_photo_url(self):
        """Return an avatar photo URL (depending on Gravatar config). This still could
        be empty, in which case the theme needs to provide an alternate photo.
        """
        if config.GRAVATAR == 'always':
            return self.get_gravatar()
        elif config.GRAVATAR == 'backup' and not self.photo_url:
            return self.get_gravatar()
        else:
            return self.photo_url

    @property
    def full_name(self):
        """Return user's full name (first name + ' ' + last name)."""
        return u'{} {}'.format(self.first_name, self.last_name)
