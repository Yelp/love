# -*- coding: utf-8 -*-
import mock
import pytest

from google.appengine.api import users

from errors import NoSuchEmployee
from loveapp.models.employee import Employee
from testing.factories import create_employee


def test_create_from_dict(mock_config, gae_testbed):
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

    assert employee is not None
    assert employee.user is not None
    assert 'john.d@foo.io' == employee.user.email()


@mock.patch('loveapp.models.employee.users.get_current_user')
def test_get_current_employee(mock_get_current_user, gae_testbed):
    employee = create_employee(username='john.d')
    mock_get_current_user.return_value = employee.user
    current_employee = Employee.get_current_employee()

    assert current_employee is not None
    assert 'john.d' == current_employee.username


@mock.patch('loveapp.models.employee.users.get_current_user')
def test_get_current_employee_raises(mock_get_current_user, gae_testbed):
    mock_get_current_user.return_value = users.User('foo@bar.io')

    with pytest.raises(NoSuchEmployee):
        Employee.get_current_employee()


def test_full_name(gae_testbed):
    employee = create_employee(first_name='Foo', last_name='Bar')
    assert 'Foo Bar' == employee.full_name


def test_gravatar_backup(mock_config, gae_testbed):
    mock_config.GRAVATAR = 'backup'
    employee = create_employee(photo_url='')
    assert employee.get_gravatar() == employee.get_photo_url()
    employee = create_employee(photo_url='http://example.com/example.jpg')
    assert employee.photo_url == employee.get_photo_url()


def test_gravatar_always(mock_config, gae_testbed):
    mock_config.GRAVATAR = 'always'
    employee = create_employee(photo_url='')
    assert employee.get_gravatar() == employee.get_photo_url()
    employee = create_employee(photo_url='http://example.com/example.jpg')
    assert employee.get_gravatar() == employee.get_photo_url()


def test_gravatar_disabled(mock_config, gae_testbed):
    mock_config.GRAVATAR = 'disabled'
    employee = create_employee(photo_url='')
    assert employee.photo_url == employee.get_photo_url()
    employee = create_employee(photo_url='http://example.com/example.jpg')
    assert employee.photo_url == employee.get_photo_url()
