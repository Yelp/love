# -*- coding: utf-8 -*-
import os
from contextlib import contextmanager

import pytest
from flask_themes2 import Themes, load_themes_from
from flask_webtest import TestApp
from google.cloud import ndb

from testing.factories.employee import create_employee


@contextmanager
def ndb_context():
    client = ndb.Client()
    with client.context():
        yield


@pytest.fixture(scope='session')
def app(datastore_emulator):
    import main

    def test_loader(app):
        return load_themes_from(os.path.join(os.path.dirname(__file__), '../themes/'))

    with ndb_context():  # the context stays valid until after the tests have executed
        main.use_ndb_middleware = False
        Themes(main.app, app_identifier='yelplove', loaders=[test_loader])
        yield TestApp(main.app)


@pytest.fixture
def recipient():
    recipient = create_employee(username='janedoe')
    yield recipient
    recipient.key.delete()
