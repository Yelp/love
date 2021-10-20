# -*- coding: utf-8 -*-
import unittest
import mock
from logic.office import REMOTE_OFFICE
from logic.office import get_all_offices
from logic.office import OfficeParser
from testing.factories import create_employee

OFFICES = {
    'Germany',
    'USA'
}


class OfficeTest(unittest.TestCase):
    # enable the datastore stub
    nosegae_datastore_v3 = True

    def setUp(self):
        self.employee_dicts = [
            {'username': 'foo1-hamburg', 'department': 'bar-team', 'office': 'Germany: Hamburg Office'},
            {'username': 'foo1-hamburg', 'department': 'bar-team', 'office': 'Germany: Remote'},
            {'username': 'foo2-hamburg', 'department': 'bar-team', 'office': 'Sweden: Remote'},
        ]
        # for employee in self.employee_dicts:
        #     create_employee(office=employee["office"], username=employee["username"])

    def _create_employees(self):
        for office in OFFICES:
            create_employee(office=office, username='{}-{}'.format('username', office))

    def test_get_all_offices(self):
        self._create_employees()
        self.assertEqual(OFFICES, set(get_all_offices()))

    @mock.patch('logic.office.yaml.safe_load', return_value=OFFICES)
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

    @mock.patch('logic.office.yaml.safe_load', return_value=OFFICES)
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
