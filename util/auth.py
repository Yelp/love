# -*- coding: utf-8 -*-
from google.appengine.api import users


def is_admin():
    return users.get_current_user() and users.is_current_user_admin()
