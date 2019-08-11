# -*- coding: utf-8 -*-
from models import Employee


def create_employee(
    username='johndoe',
    department='Engineering',
    first_name='John',
    last_name='Doe',
    photo_url=None,
    office=None,
):

    if photo_url is None:
        photo_url = 'http://example.com/photos/{0}.jpg'.format(username)

    return Employee.create_from_dict({
        'username': username,
        'department': department,
        'first_name': first_name,
        'last_name': last_name,
        'photo_url': photo_url,
        'office': office,
    })
