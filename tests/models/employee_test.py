# -*- coding: utf-8 -*-
import mock
import unittest

from google.appengine.api import users

from errors import NoSuchEmployee
from models.employee import Employee
from testing.factories import create_employee


class EmployeeTest(unittest.TestCase):
    # enable the datastore stub
    nosegae_datastore_v3 = True

    @mock.patch('models.employee.config')
    def test_create_from_dict(self, mock_config):
        mock_config.DOMAIN = 'foo.io'

        employee_dict = dict(
            username='john.d',
            first_name='John',
            last_name='Doe',
            department='Accounting',
            office='USA CA SF New Montgomery',
            photos=[],
        )
        employee = Employee.create_from_dict(employee_dict)

        self.assertIsNotNone(employee)
        self.assertIsNotNone(employee.user)
        self.assertEqual('john.d@foo.io', employee.user.email())

    @mock.patch('models.employee.users.get_current_user')
    def test_get_current_employee(self, mock_get_current_user):
        employee = create_employee(username='john.d')
        mock_get_current_user.return_value = employee.user
        current_employee = Employee.get_current_employee()

        self.assertIsNotNone(current_employee)
        self.assertEqual('john.d', current_employee.username)

    @mock.patch('models.employee.users.get_current_user')
    def test_get_current_employee_raises(self, mock_get_current_user):
        mock_get_current_user.return_value = users.User('foo@bar.io')

        with self.assertRaises(NoSuchEmployee):
            Employee.get_current_employee()

    def test_full_name(self):
        employee = create_employee(first_name='Foo', last_name='Bar')
        self.assertEqual('Foo Bar', employee.full_name)

    def test_refresh_index_employees(self):
        employee1 = create_employee(username='Foo')
        employee2 = create_employee(username='Foo2')
        Employee.refresh_indexes()
        employees = Employee.query().fetch()
        self.assertEqual(len(employees), 2)
        self.assertEqual(Employee.query(Employee.username == employee1.username).fetch()[0].key, employee1.key)
        self.assertEqual(Employee.query(Employee.username == employee2.username).fetch()[0].key, employee2.key)

    @mock.patch('models.employee.config')
    def test_gravatar_backup(self, mock_config):
        mock_config.GRAVATAR = 'backup'
        employee = create_employee(photo_url='')
        self.assertEqual(employee.get_gravatar(), employee.get_photo_url())
        employee = create_employee(photo_url='http://example.com/example.jpg')
        self.assertEqual(employee.photo_url, employee.get_photo_url())

    @mock.patch('models.employee.config')
    def test_gravatar_always(self, mock_config):
        mock_config.GRAVATAR = 'always'
        employee = create_employee(photo_url='')
        self.assertEqual(employee.get_gravatar(), employee.get_photo_url())
        employee = create_employee(photo_url='http://example.com/example.jpg')
        self.assertEqual(employee.get_gravatar(), employee.get_photo_url())

    @mock.patch('models.employee.config')
    def test_gravatar_disabled(self, mock_config):
        mock_config.GRAVATAR = 'disabled'
        employee = create_employee(photo_url='')
        self.assertEqual(employee.photo_url, employee.get_photo_url())
        employee = create_employee(photo_url='http://example.com/example.jpg')
        self.assertEqual(employee.photo_url, employee.get_photo_url())
