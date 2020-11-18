# -*- coding: utf-8 -*-
import unittest
from models.employee import REMOTE_OFFICE
from logic.office import get_all_offices
from testing.factories import create_employee


OFFICES = {
    'OFFice 1 Hamburg',
    'Germany Berlin',
}

OFFICE_NAME = 'Office 1'


class OfficeTest(unittest.TestCase):
    # enable the datastore stub
    nosegae_datastore_v3 = True

    def _create_employees(self):
        for office in OFFICES:
            create_employee(office=office, username='{}-{}'.format('username', office))

    def test_get_all_offices(self):
        self._create_employees()
        self.assertEqual({OFFICE_NAME, REMOTE_OFFICE}, set(get_all_offices()))
