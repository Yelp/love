# -*- coding: utf-8 -*-
import unittest

import mock
import pytest

from loveapp.logic.office import get_all_offices
from loveapp.logic.office import OfficeParser
from loveapp.logic.office import REMOTE_OFFICE
from testing.factories import create_employee

OFFICES = {
    'Germany',
    'USA'
}


class TestOffice(unittest.TestCase):

    def setUp(self):
        self.employee_dicts = [
            {'username': 'foo1-hamburg', 'department': 'bar-team', 'office': 'Germany: Hamburg Office'},
            {'username': 'foo2-hamburg', 'department': 'bar-team', 'office': 'Germany: Remote'},
            {'username': 'foo3-hamburg', 'department': 'bar-team', 'office': 'Sweden: Remote'},
        ]

    def _create_employees(self):
        for office in OFFICES:
            create_employee(office=office, username='{}-{}'.format('username', office))

    @pytest.mark.usefixtures('gae_testbed')
    def test_get_all_offices(self):
        self._create_employees()
        assert OFFICES == set(get_all_offices())

    @mock.patch('loveapp.logic.office.yaml.safe_load', return_value=OFFICES)
    def test_employee_parser_no_team_match(self, mock_offices):
        office_parser = OfficeParser()
        self.assertEqual(
            office_parser.get_office_name(
                self.employee_dicts[0]['office'],
            ),
            'Germany',
        )
        self.assertEqual(
            office_parser.get_office_name(
                self.employee_dicts[1]['office'],
            ),
            'Germany',
        )
        self.assertEqual(
            office_parser.get_office_name(
                self.employee_dicts[2]['office'],
            ),
            REMOTE_OFFICE,
        )
        mock_offices.assert_called_once()

    @mock.patch('loveapp.logic.office.yaml.safe_load', return_value=OFFICES)
    def test_employee_parser_with_team_match(self, mock_offices):
        office_parser = OfficeParser(self.employee_dicts)
        for employee in self.employee_dicts:
            self.assertEqual(
                office_parser.get_office_name(
                    employee['office'],
                    employee_department=employee['department'],
                ),
                'Germany',
            )
        mock_offices.assert_called_once()
