# -*- coding: utf-8 -*-
import mock
import os
from contextlib import contextmanager

import pytest
from google.cloud import ndb
from flask_themes2 import Themes, load_themes_from
from flask_webtest import TestApp

import main
from testing.factories import create_employee


class YelpLoveTestCase:

    @contextmanager
    def ndb_context(self):
        client = ndb.Client()
        with client.context():
            yield

    @pytest.fixture(scope='session')
    def app(self, datastore_emulator):
        def test_loader(app):
            return load_themes_from(os.path.join(os.path.dirname(__file__), '../themes/'))

        with self.ndb_context():  # the context stays valid until after the tests have executed
            main.use_ndb_middleware = False
            Themes(main.app, app_identifier='yelplove', loaders=[test_loader])
            yield TestApp(main.app)

    def assert_requires_admin(self, response):
        assert response.status_int == 401

    def assert_has_csrf(self, form, session):
        """Make sure the response form contains the correct CSRF token.

        :param form: a form entry from response.forms
        :param session: response.session
        """
        assert form.get('_csrf_token')
        assert form['_csrf_token'].value == session['_csrf_token']

    def add_csrf_token_to_session(self, app):
        csrf_token = 'MY_TOKEN'
        with app.session_transaction() as session:
            session['_csrf_token'] = csrf_token
        return csrf_token


class LoggedInUserBaseTest(YelpLoveTestCase):

    @pytest.fixture(autouse=True)
    def current_user(self):
        with mock.patch('models.employee.config') as mock_config:
            mock_config.DOMAIN = 'example.com'
            current_user = create_employee(username='johndoe')
            yield current_user

        current_user.key.delete()


class LoggedInAdminBaseTest(YelpLoveTestCase):

    @pytest.fixture(autouse=True)
    def current_user(self):
        with mock.patch('models.employee.config') as mock_config:
            mock_config.DOMAIN = 'example.com'
            current_user = create_employee(username='johndoe', is_admin=True)
            yield current_user

        current_user.key.delete()
