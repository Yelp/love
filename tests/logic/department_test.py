# -*- coding: utf-8 -*-
from loveapp.logic.department import get_all_departments
from testing.factories import create_employee

DEPARTMENTS = [
    'Department 1',
    'Department 2',
    'Department 3',
    'Department 4',
    'Department 4',
    'Department 5',
]


def test_get_all_departments(gae_testbed):
    for department in DEPARTMENTS:
        create_employee(department=department, username='{}-{}'.format('username', department))

    assert set(DEPARTMENTS) == set(get_all_departments())
