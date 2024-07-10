# -*- coding: utf-8 -*-
import unittest

import mock
import pytest

import loveapp.logic.love
from errors import TaintedLove
from loveapp.config import CompanyValue
from testing.factories import create_alias_with_employee_username
from testing.factories import create_employee


@pytest.mark.usefixtures('gae_testbed')
class TestSendLoves(unittest.TestCase):

    def setUp(self):
        self.alice = create_employee(username='alice')
        self.bob = create_employee(username='bob')
        self.carol = create_employee(username='carol')
        self.message = 'hallo'

    @mock.patch('google.appengine.api.taskqueue.add', autospec=True)
    def test_send_loves(self, mock_taskqueue_add):
        loveapp.logic.love.send_loves(
            set(['bob', 'carol']),
            self.message,
            sender_username='alice',
        )

        loves_for_bob = loveapp.logic.love.get_love(None, 'bob').get_result()
        self.assertEqual(len(loves_for_bob), 1)
        self.assertEqual(loves_for_bob[0].sender_key, self.alice.key)
        self.assertEqual(loves_for_bob[0].message, self.message)

        loves_for_carol = loveapp.logic.love.get_love(None, 'carol').get_result()
        self.assertEqual(len(loves_for_carol), 1)
        self.assertEqual(loves_for_carol[0].sender_key, self.alice.key)
        self.assertEqual(loves_for_carol[0].message, self.message)

    def test_invalid_sender(self):
        with self.assertRaises(TaintedLove):
            loveapp.logic.love.send_loves(
                set(['alice']),
                'hallo',
                sender_username='wwu',
            )

    @mock.patch('google.appengine.api.taskqueue.add', autospec=True)
    def test_sender_is_a_recipient(self, mock_taskqueue_add):
        loveapp.logic.love.send_loves(
            set(['bob', 'alice']),
            self.message,
            sender_username='alice',
        )

        loves_for_bob = loveapp.logic.love.get_love('alice', 'bob').get_result()
        self.assertEqual(len(loves_for_bob), 1)
        self.assertEqual(loves_for_bob[0].message, self.message)

        loves_for_alice = loveapp.logic.love.get_love(None, 'alice').get_result()
        self.assertEqual(loves_for_alice, [])

    def test_sender_is_only_recipient(self):
        with self.assertRaises(TaintedLove):
            loveapp.logic.love.send_loves(
                set(['alice']),
                self.message,
                sender_username='alice',
            )

    def test_invalid_recipient(self):
        with self.assertRaises(TaintedLove):
            loveapp.logic.love.send_loves(
                set(['bob', 'dean']),
                'hallo',
                sender_username='alice',
            )

        loves_for_bob = loveapp.logic.love.get_love('alice', 'bob').get_result()
        self.assertEqual(loves_for_bob, [])

    @mock.patch('google.appengine.api.taskqueue.add', autospec=True)
    def test_send_loves_with_alias(self, mock_taskqueue_add):
        message = 'Loving your alias'
        create_alias_with_employee_username(name='bobby', username=self.bob.username)

        loveapp.logic.love.send_loves(['bobby'], message, sender_username=self.carol.username)

        loves_for_bob = loveapp.logic.love.get_love('carol', 'bob').get_result()
        self.assertEqual(len(loves_for_bob), 1)
        self.assertEqual(loves_for_bob[0].sender_key, self.carol.key)
        self.assertEqual(loves_for_bob[0].message, message)

    def test_send_loves_with_alias_and_username_for_same_user(self):
        create_alias_with_employee_username(name='bobby', username=self.bob.username)

        with self.assertRaises(TaintedLove):
            loveapp.logic.love.send_loves(['bob', 'bobby'], 'hallo', sender_username='alice')

        loves_for_bob = loveapp.logic.love.get_love('alice', 'bob').get_result()
        self.assertEqual(loves_for_bob, [])

    @mock.patch('loveapp.util.company_values.config')
    @mock.patch('google.appengine.api.taskqueue.add', autospec=True)
    def test_send_love_with_value_hashtag(self, mock_taskqueue_add, mock_config):
        mock_config.COMPANY_VALUES = [
            CompanyValue('AWESOME', 'awesome', ['awesome'])
        ]
        message = 'Loving your alias #Awesome'
        create_alias_with_employee_username(name='bobby', username=self.bob.username)
        loveapp.logic.love.send_loves(['bobby'], message, sender_username=self.carol.username)

        loves_for_bob = loveapp.logic.love.get_love('carol', 'bob').get_result()
        self.assertEqual(len(loves_for_bob), 1)
        self.assertEqual(loves_for_bob[0].company_values, ['AWESOME'])
