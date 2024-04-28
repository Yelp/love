# -*- coding: utf-8 -*-
import mock
import pytest

from google.appengine.ext import testbed
from loveapp import create_app


@pytest.fixture
def app():  # noqa
    app = create_app()

    with app.app_context():
        yield app


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

    yield

    tb.deactivate()
