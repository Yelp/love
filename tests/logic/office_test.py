# -*- coding: utf-8 -*-
import unittest


from logic.office import get_all_offices
from logic.office import get_all_offices_compressed
from testing.factories import create_employee

OFFICES = [
    'United Kingdom London',
    'United Kingdom',
    'USA NY Madison Ave',
    'USA NY Fifth Ave',
    'USA CA SF New Montgomery',
    'USA CA SF Hawthorne',
    'USA CA SF',
    'Germany Hamburg',
    'Germany Hamburg',
    'Czech Republic',
    'Canada Toronto',
    'Canada',
]


class OfficeTest(unittest.TestCase):
    # enable the datastore stub
    nosegae_datastore_v3 = True

    def _create_employees(self):
        for office in OFFICES:
            create_employee(office=office, username='{}-{}'.format('username', office))

    def test_get_all_offices(self):
        self._create_employees()
        self.assertEqual(set(OFFICES), set(get_all_offices()))

    def test_get_all_offices_compressed(self):
        self._create_employees()
        self.assertEqual(
            set(
                [
                    'Canada',
                    'United Kingdom',
                    'USA NY Madison Ave',
                    'Germany Hamburg',
                    'USA NY Fifth Ave',
                    'USA CA SF',
                    'Czech Republic'
                ],
            ),
            set(get_all_offices_compressed()),
        )
