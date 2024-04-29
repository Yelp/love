# -*- coding: utf-8 -*-
import mock
import unittest
import pytest


from testing.factories import create_employee


@pytest.mark.usefixtures('gae_testbed', 'app')
class YelpLoveTestCase(unittest.TestCase):

    def assertRequiresLogin(self, response):
        self.assertEqual(response.status_int, 302)
        self.assert_(
            response.headers['Location'].startswith('https://www.google.com/accounts/Login'),
            'Unexpected Location header: {0}'.format(response.headers['Location']),
        )

    def assertRequiresAdmin(self, response):
        self.assertEqual(response.status_int, 401)

    def assertHasCsrf(self, form, session):
        """Make sure the response form contains the correct CSRF token.

        :param form: a form entry from response.forms
        :param session: response.session
        """
        self.assertIsNotNone(form.get('_csrf_token'))
        self.assertEqual(
            form['_csrf_token'].value, session['_csrf_token'],
        )

    def addCsrfTokenToSession(self):
        csrf_token = 'MY_TOKEN'
        with self.app.session_transaction() as session:
            session['_csrf_token'] = csrf_token
        return csrf_token


class LoggedInUserBaseTest(YelpLoveTestCase):

    nosegae_datastore_v3 = True
    nosegae_datastore_v3_kwargs = {
        'datastore_file': '/tmp/nosegae.sqlite3',
        'use_sqlite': True
    }

    nosegae_user = True
    nosegae_user_kwargs = dict(
        USER_ID='johndoe',
        USER_EMAIL='johndoe@example.com',
        USER_IS_ADMIN='0',
    )

    @mock.patch('models.employee.config')
    def setUp(self, mock_config):
        mock_config.DOMAIN = 'example.com'
        self.current_user = create_employee(username='johndoe')

    def tearDown(self):
        self.current_user.key.delete()


class LoggedInAdminBaseTest(LoggedInUserBaseTest):

    nosegae_user_kwargs = dict(
        USER_ID='johndoe',
        USER_EMAIL='johndoe@example.com',
        USER_IS_ADMIN='1',
    )
