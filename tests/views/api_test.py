# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import unittest

import logic.employee
import logic.love
from models import AccessKey
from testing.factories import create_alias_with_employee_username
from testing.factories import create_employee
from testing.util import YelpLoveTestCase
from webtest.app import AppError


class _ApiKeyRequiredTestCase(YelpLoveTestCase):
    nosegae_datastore_v3 = True
    nosegae_memcache = True
    nosegae_taskqueue = True
    successful_response_code = 200

    @classmethod
    def setUpClass(cls):
        if cls is _ApiKeyRequiredTestCase:
            raise unittest.SkipTest('_ApiKeyRequiredTestCase is a base class')
        super(_ApiKeyRequiredTestCase, cls).setUpClass()

    def do_request(self, api_key):
        raise NotImplementedError('Implement this method with behavior which'
                                  ' requires an API key and returns the response')

    def test_with_api_key(self):
        api_key = AccessKey.create('test key').access_key
        response = self.do_request(api_key)
        self.assertEqual(response.status_int, self.successful_response_code)

    def test_without_api_key(self):
        bad_api_key = AccessKey.generate_uuid()
        with self.assertRaises(AppError) as caught:
            self.do_request(bad_api_key)

        self.assert_(caught.exception.message.startswith('Bad response: 401'),
                     'Expected request without valid API key to return 401')


class AutocompleteTest(_ApiKeyRequiredTestCase):
    nosegae_memcache = True
    nosegae_datastore_v3 = True
    nosegae_search = True

    def setUp(self):
        super(AutocompleteTest, self).setUp()
        create_employee(username='alice')
        create_employee(username='alex')
        create_employee(username='bob')
        create_employee(username='carol')
        logic.employee.rebuild_index()
        self.api_key = AccessKey.create('autocomplete key').access_key

    def test_autocomplete(self):
        self._test_autocomplete('a', ['alice', 'alex'])
        self._test_autocomplete('b', ['bob'])
        self._test_autocomplete('c', ['carol'])
        self._test_autocomplete('stupidprefix', [])
        self._test_autocomplete('', [])

    def _test_autocomplete(self, prefix, expected_values, api_key=None):
        if api_key is None:
            api_key = self.api_key
        response = self.app.get('/api/autocomplete', {'term': prefix, 'api_key': api_key})
        received_values = set(item['value'] for item in response.json)
        self.assertEqual(set(expected_values), received_values)
        return response

    def do_request(self, api_key):
        return self._test_autocomplete('test', [], api_key)


class GetLoveTest(_ApiKeyRequiredTestCase):

    def setUp(self):
        super(GetLoveTest, self).setUp()
        create_employee(username='alice')
        create_employee(username='bob')
        logic.love.send_loves(['bob', ], 'Care Bear Stare!', 'alice')

    def do_request(self, api_key):
        query_params = {
            'sender': 'alice',
            'recipient': 'bob',
            'limit': 1,
            'api_key': api_key,
        }
        response = self.app.get('/api/love', query_params)
        response_data = response.json
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['sender'], 'alice')
        self.assertEqual(response_data[0]['recipient'], 'bob')
        return response


class SendLoveTest(_ApiKeyRequiredTestCase):
    successful_response_code = 201

    def setUp(self):
        super(SendLoveTest, self).setUp()
        create_employee(username='alice')
        create_employee(username='bob')

    def do_request(self, api_key):
        form_values = {
            'sender': 'alice',
            'recipient': 'bob',
            'message': 'Care Bear Stare!',
            'api_key': api_key,
        }
        response = self.app.post('/api/love', form_values)
        self.assertTrue('Love sent to bob! Share:' in response.body)
        return response


class SendLoveFailTest(YelpLoveTestCase):
    nosegae_datastore_v3 = True
    nosegae_memcache = True
    nosegae_taskqueue = True

    def setUp(self):
        self.api_key = AccessKey.create('test key').access_key
        create_employee(username='bob')
        create_alias_with_employee_username(name='bobby', username='bob')
        create_employee(username='alice')

    def test_send_loves_with_alias_and_username_for_same_user(self):
        form_values = {
            'sender': 'alice',
            'recipient': 'bob,bobby',
            'message': 'Alias',
            'api_key': self.api_key,
        }

        with self.assertRaises(AppError) as caught:
            self.app.post('/api/love', form_values)

        self.assert_(
            caught.exception.message.startswith('Bad response: 418'),
            'Expected request to return 418',
        )
        self.assertIn('send love to a user multiple times', caught.exception.message)


class GetLeaderboardTest(_ApiKeyRequiredTestCase):

    def setUp(self):
        super(GetLeaderboardTest, self).setUp()
        create_employee(username='alice')
        create_employee(username='bob')
        logic.love.send_loves(['bob', ], 'Care Bear Stare!', 'alice')

    def do_request(self, api_key):
        query_params = {
            'api_key': api_key,
            'department': 'Engineering',
        }
        response = self.app.get('/api/leaderboard', query_params)
        response_data = response.json
        top_loved = response_data[0]
        top_lover = response_data[1]
        self.assertEqual(len(response_data), 2)
        self.assertEqual(len(top_loved), 1)
        self.assertEqual(len(top_lover), 1)
        self.assertEqual(top_loved[0].get('username'), 'bob')
        self.assertEqual(top_lover[0].get('username'), 'alice')
        return response
