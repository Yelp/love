# -*- coding: utf-8 -*-

from models import Alias
from models import Employee


def get_alias(alias):
    return Alias.query(Alias.name == alias).get()


def save_alias(alias, username):
    alias = Alias(
        name=alias,
        owner_key=Employee.get_key_for_username(username),
    )
    alias.put()
    return alias


def delete_alias(alias_id):
    alias = Alias.get_by_id(alias_id)
    alias.key.delete()


def name_for_alias(alias_name):
    alias = Alias.query(Alias.name == alias_name).get()
    if alias:
        employee = alias.owner_key.get()
        if employee:
            return employee.username
    else:
        return alias_name
