# -*- coding: utf-8 -*-
from loveapp.models import Alias
from loveapp.models import Employee


def create_alias_with_employee_username(
    name='jda',
    username='jd',
):
    alias = Alias(
        name=name,
        owner_key=Employee.get_key_for_username(username),
    )
    alias.put()
    return alias


def create_alias_with_employee_key(
    name='jda',
    employee_key='jd',
):
    alias = Alias(
        name=name,
        owner_key=employee_key,
    )
    alias.put()
    return alias
