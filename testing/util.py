# -*- coding: utf-8 -*-
import mock
import pytest
from bs4 import BeautifulSoup

from testing.factories import create_employee


class YelpLoveTestCase():

    def assertRequiresLogin(self, response):
        assert response.status_code == 302
        assert response.headers['Location'].startswith('https://www.google.com/accounts/Login'), \
            'Unexpected Location header: {0}'.format(response.headers['Location'])

    def assertRequiresAdmin(self, response):
        response.status_code == 401

    def assertHasCsrf(self, response, form_class, session):
        """Make sure the response form contains the correct CSRF token.

        :param form: a form entry from response.forms
        :param session: response.session
        """
        soup = BeautifulSoup(response.data, 'html.parser')
        csrf_token = soup.find('form', class_=form_class).\
            find('input', attrs={'name': '_csrf_token'}).\
            get('value')
        assert csrf_token is not None
        assert csrf_token == session['_csrf_token']

    def addCsrfTokenToSession(self, client):
        csrf_token = 'MY_TOKEN'
        with client.session_transaction() as session:
            session['_csrf_token'] = csrf_token
        return csrf_token


class LoggedInUserBaseTest(YelpLoveTestCase):

    @pytest.fixture(autouse=True)
    def logged_in_user(self, gae_testbed):
        self.logged_in_employee = create_employee(username='johndoe')
        with mock.patch('loveapp.util.decorators.users.get_current_user') as mock_get_current_user:
            mock_get_current_user.return_value = self.logged_in_employee.user
            yield self.logged_in_employee
        self.logged_in_employee.key.delete()


class LoggedInAdminBaseTest(LoggedInUserBaseTest):
    @pytest.fixture(autouse=True)
    def logged_in_admin(self, gae_testbed):
        self.logged_in_employee = create_employee(username='johndoe')
        with mock.patch('loveapp.util.decorators.users.is_current_user_admin') as mock_is_current_user_admin:
            mock_is_current_user_admin.return_value = True
            yield self.logged_in_employee
        self.logged_in_employee.key.delete()
