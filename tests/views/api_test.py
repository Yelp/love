# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import pytest

import mock

import loveapp.logic.employee
import loveapp.logic.love
from loveapp.models import AccessKey
from loveapp.views.api import LOVE_FAILED_STATUS_CODE
from testing.factories import create_alias_with_employee_username
from testing.factories import create_employee


@pytest.fixture
def api_key(gae_testbed_class_scope):
    return AccessKey.create('autocomplete key').access_key


class _ApiKeyRequiredTestCase():
    successful_response_code = 200

    def do_request(self, api_key):
        raise NotImplementedError('Implement this method with behavior which'
                                  ' requires an API key and returns the response')

    def test_with_api_key(self, gae_testbed, client, api_key):
        response = self.do_request(client, api_key)
        assert response.status_code == self.successful_response_code

    def test_without_api_key(self, gae_testbed, client):
        bad_api_key = AccessKey.generate_uuid()
        response = self.do_request(client, bad_api_key)
        assert response.status == '401 UNAUTHORIZED'


class TestAutocomplete(_ApiKeyRequiredTestCase):
    @pytest.fixture(scope='class', autouse=True)
    def create_employees(self, gae_testbed_class_scope):
        create_employee(username='alice')
        create_employee(username='alex')
        create_employee(username='bob')
        create_employee(username='carol')
        with mock.patch('loveapp.logic.employee.memory_usage', autospec=True):
            loveapp.logic.employee.rebuild_index()

    def do_request(self, client, api_key):
        return client.get(
            'api/autocomplete',
            query_string={'term': ''},
            data={'api_key': api_key}
        )

    @pytest.mark.parametrize('prefix, expected_values', [
        ('a', ['alice', 'alex']),
        ('b', ['bob']),
        ('c', ['carol']),
        ('', []),
        ('stupidprefix', []),
    ])
    def test_autocomplete(gae_testbed_class_scope, client, api_key, prefix, expected_values):
        api_key = AccessKey.create('autocomplete key').access_key
        response = client.get('/api/autocomplete', query_string={'term': prefix}, data={'api_key': api_key})
        received_values = set(item['value'] for item in response.json)
        assert set(expected_values) == received_values


class TestGetLove(_ApiKeyRequiredTestCase):
    @pytest.fixture(autouse=True)
    def create_employees(self, gae_testbed):
        create_employee(username='alice')
        create_employee(username='bob')

    def do_request(self, client, api_key):
        query_params = {
            'sender': 'alice',
            'recipient': 'bob',
            'limit': 1
        }
        return client.get(
            '/api/love',
            query_string=query_params,
            data={'api_key': api_key}
        )

    def test_get_love(self, gae_testbed_class_scope, client, api_key):
        with mock.patch('loveapp.logic.event.add_event'):
            loveapp.logic.love.send_loves(['bob', ], 'Care Bear Stare!', 'alice')
        response = self.do_request(client, api_key)
        response_data = response.json
        assert len(response_data) == 1
        assert response_data[0]['sender'] == 'alice'
        assert response_data[0]['recipient'] == 'bob'


class TestSendLove(_ApiKeyRequiredTestCase):
    successful_response_code = 201

    @pytest.fixture(autouse=True)
    def create_employees(self, gae_testbed):
        create_employee(username='alice')
        create_employee(username='bob')

    def do_request(self, client, api_key):
        form_values = {
            'sender': 'alice',
            'recipient': 'bob',
            'message': 'Care Bear Stare!',
            'api_key': api_key,
        }
        with mock.patch('loveapp.logic.event.add_event'):
            response = client.post('/api/love', data=form_values)
        return response

    def test_send_love(self, gae_testbed_class_scope, client, api_key):
        response = self.do_request(client, api_key)
        assert 'Love sent to bob! Share:' in response.data.decode()

    def test_send_loves_with_alias_and_username_for_same_user(self, gae_testbed_class_scope, client, api_key):
        create_alias_with_employee_username(name='bobby', username='bob')
        form_values = {
            'sender': 'alice',
            'recipient': 'bob,bobby',
            'message': 'Alias',
            'api_key': api_key,
        }

        response = client.post('/api/love', data=form_values)
        assert response.status_code == LOVE_FAILED_STATUS_CODE
        assert 'send love to a user multiple times' in response.data.decode()


class TestGetLeaderboard(_ApiKeyRequiredTestCase):
    @pytest.fixture(autouse=True)
    def create_employees(self, gae_testbed):
        create_employee(username='alice')
        create_employee(username='bob')
        with mock.patch('loveapp.logic.event.add_event'):
            loveapp.logic.love.send_loves(['bob', ], 'Care Bear Stare!', 'alice')

    def do_request(self, client, api_key):
        query_params = {
            'department': 'Engineering',
        }
        return client.get(
            '/api/leaderboard',
            query_string=query_params,
            data={'api_key': api_key}
        )

    def test_get_leaderboard(self, gae_testbed_class_scope, client, api_key):
        response_data = self.do_request(client, api_key).json
        top_loved = response_data.get('top_loved')
        top_lover = response_data.get('top_lover')
        assert len(response_data) == 2
        assert len(top_loved) == 1
        assert len(top_lover) == 1
        assert top_loved[0].get('username') == 'bob'
        assert top_lover[0].get('username') == 'alice'
