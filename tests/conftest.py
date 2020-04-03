# -*- coding: utf-8 -*-
import os
import subprocess
import time
import urllib
from functools import wraps
from unittest import mock

import pytest


DATASTORE_HOST = 'http://localhost:8081'

_datastore_emulator_process = None
_oidc_patcher = None
_mock_OpenIDConnect = None

mock_require_login_call_count = 0


def oidc_require_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        global mock_require_login_call_count
        mock_require_login_call_count += 1
        print('Running the wrapper!')
        return func(*args, **kwargs)
    return wrapper


_mock_oidc = mock.Mock(name='mock oidc', require_login=oidc_require_login)


def pytest_sessionstart(session):
    global _datastore_emulator_process, _oidc_patcher, _mock_oidc, _mock_OpenIDConnect

    _datastore_emulator_process = subprocess.Popen(
        ['gcloud beta emulators datastore start --no-store-on-disk'], shell=True)
    # we need to set these before main is imported
    os.environ['DATASTORE_DATASET'] = 'yelplove'
    os.environ['DATASTORE_EMULATOR_HOST'] = 'localhost:8081'
    os.environ['DATASTORE_EMULATOR_HOST_PATH'] = 'localhost:8081/datastore'
    os.environ['DATASTORE_HOST'] = DATASTORE_HOST
    os.environ['DATASTORE_PROJECT_ID'] = 'yelplove'

    _oidc_patcher = mock.patch('flask_oidc.OpenIDConnect', return_value=_mock_oidc)
    _mock_OpenIDConnect = _oidc_patcher.start()
    _mock_oidc.user_getfield.return_value = 'johndoe@example.com'


def pytest_sessionfinish(session, exitstatus):
    _oidc_patcher.stop()
    try:
        urllib.request.urlopen(urllib.request.Request(DATASTORE_HOST + '/shutdown', method='POST'), timeout=1)
    except (urllib.error.URLError):
        pass
    _datastore_emulator_process.terminate()


@pytest.fixture(scope='session')
def datastore_emulator():
    # wait until the datastore emulator is ready
    start = time.time()
    while time.time() < start + 10:  # not using monotonic as it is not a pure python package
        try:
            urllib.request.urlopen(DATASTORE_HOST + '/', timeout=2)
            return
        except urllib.error.URLError:  # pragma: no cover
            time.sleep(0.1)

    raise AssertionError('Datastore emulator did not start up properly.')


@pytest.fixture
def mock_oidc():
    global mock_require_login_call_count
    _mock_oidc.reset_mock()
    mock_require_login_call_count = 0
    return _mock_oidc
