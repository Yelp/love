# -*- coding: utf-8 -*-
import mock
import unittest

from google.appengine.api import users

from errors import NoSuchEmployee
from models.employee import Employee
from testing.factories import create_employee


class TestEmployee(unittest.TestCase):
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
            photos=[]
        )
        employee = Employee.create_from_dict(employee_dict)

        assert employee is not None
        assert employee.user is not None
        assert 'john.d@foo.io' == employee.user.email()

    @mock.patch('models.employee.users.get_current_user')
    def test_get_current_employee(self, mock_get_current_user):
        employee = create_employee(username='john.d')
        mock_get_current_user.return_value = employee.user
        current_employee = Employee.get_current_employee()

        assert current_employee is not None
        assert 'john.d' == current_employee.username

    @mock.patch('models.employee.users.get_current_user')
    def test_get_current_employee_raises(self, mock_get_current_user):
        mock_get_current_user.return_value = users.User('foo@bar.io')

        with self.assertRaises(NoSuchEmployee):
            Employee.get_current_employee()

    def test_full_name(self):
        employee = create_employee(first_name='Foo', last_name='Bar')
        assert 'Foo Bar' == employee.full_name

    @mock.patch('models.employee.config')
    def test_gravatar_backup(self, mock_config):
        mock_config.GRAVATAR = 'backup'
        employee = create_employee(photo_url='')
        assert employee.get_gravatar() == employee.get_photo_url()
        employee = create_employee(photo_url='http://example.com/example.jpg')
        assert employee.photo_url == employee.get_photo_url()

    @mock.patch('models.employee.config')
    def test_gravatar_always(self, mock_config):
        mock_config.GRAVATAR = 'always'
        employee = create_employee(photo_url='')
        assert employee.get_gravatar() == employee.get_photo_url()
        employee = create_employee(photo_url='http://example.com/example.jpg')
        assert employee.get_gravatar() == employee.get_photo_url()

    @mock.patch('models.employee.config')
    def test_gravatar_disabled(self, mock_config):
        mock_config.GRAVATAR = 'disabled'
        employee = create_employee(photo_url='')
        assert employee.photo_url == employee.get_photo_url()
        employee = create_employee(photo_url='http://example.com/example.jpg')
        assert employee.photo_url == employee.get_photo_url()
