# -*- coding: utf-8 -*-
from models import Employee


def create_employee(
    username='johndoe',
    department='Engineering',
    first_name='John',
    last_name='Doe',
):

    return Employee.create_from_dict({
        'username': username,
        'department': department,
        'first_name': first_name,
        'last_name': last_name,
        'photo_url': 'http://exmaple.com/photos/{0}.jpg'.format(username),
    })
