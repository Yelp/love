# -*- coding: utf-8 -*-
import os

import mock
import pytest

from flask_themes2 import load_themes_from
from flask import template_rendered

from google.appengine.ext import testbed
from loveapp import create_app


@pytest.fixture
def app():  # noqa
    # do we need this? for what?
    def test_loader(app):
        return load_themes_from(os.path.join(os.path.dirname(__file__), '../loveapp/themes/'))
    app = create_app(theme_loaders=[test_loader])

    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def recorded_templates(app):
    recorded = []

    def record(sender, template, context, **extra):
        recorded.append((template, context))

    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)


@pytest.fixture
def mock_config():
    with mock.patch('loveapp.config') as mock_config:
        mock_config.DOMAIN = 'example.com'
        yield mock_config


@pytest.fixture(scope='function')
def gae_testbed():
    tb = testbed.Testbed()
    tb.activate()
    tb.init_memcache_stub()
    tb.init_datastore_v3_stub()
    tb.init_search_stub()
    tb.init_taskqueue_stub()
    tb.init_user_stub()

    yield tb

    tb.deactivate()
