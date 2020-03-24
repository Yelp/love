# -*- coding: utf-8 -*-
from models import Employee
from main import oidc


def is_admin():
    username = oidc.user_getfield('email').split('@')[0]
    isAdmin = Employee.query(
        Employee.username == username, Employee.is_admin == True  # noqa
    ).get()
    return bool(isAdmin)
