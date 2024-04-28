# -*- coding: utf-8 -*-
import unittest


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


class DepartmentTest(unittest.TestCase):
    # enable the datastore stub
    nosegae_datastore_v3 = True

    def test_get_all_departments(self):
        for department in DEPARTMENTS:
            create_employee(department=department, username='{}-{}'.format('username', department))

        self.assertEqual(set(DEPARTMENTS), set(get_all_departments()))
