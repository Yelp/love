# -*- coding: utf-8 -*-
import datetime
import unittest

import pytest

import loveapp.logic.love
import loveapp.logic.love_link
from errors import NoSuchLoveLink
from testing.factories import create_employee
from testing.factories import create_love_link


@pytest.mark.usefixtures('gae_testbed')
class LoveLinkTest(unittest.TestCase):

    def setUp(self):
        self.link = create_love_link(hash_key='HeLLo', recipient_list='johndoe,janedoe', message='well hello there')
        self.princessbubblegum = create_employee(username='princessbubblegum')

    def test_get_love_link(self):
        link = loveapp.logic.love_link.get_love_link('HeLLo')
        self.assertEqual(link.hash_key, 'HeLLo')
        self.assertEqual(link.recipient_list, 'johndoe,janedoe')
        self.assertEqual(link.message, 'well hello there')

    def test_create_love_link(self):
        link = loveapp.logic.love_link.create_love_link('jake', "it's adventure time!")
        self.assertEqual(link.recipient_list, 'jake')
        self.assertEqual(link.message, "it's adventure time!")

    def test_add_recipient(self):
        link = loveapp.logic.love_link.create_love_link('finn', 'Mathematical!')

        loveapp.logic.love_link.add_recipient(link.hash_key, 'princessbubblegum')
        new_link = loveapp.logic.love_link.get_love_link(link.hash_key)

        self.assertEqual(new_link.recipient_list, 'finn, princessbubblegum')

    def test_love_links_cleanup(self):
        new_love = loveapp.logic.love_link.create_love_link('jake', "I'm new love!")
        old_love = loveapp.logic.love_link.create_love_link('finn', "I'm old love :(")
        old_love.timestamp = datetime.datetime.now() - datetime.timedelta(days=31)
        old_love.put()

        loveapp.logic.love_link.love_links_cleanup()
        db_love = loveapp.logic.love_link.get_love_link(new_love.hash_key)

        self.assertEqual(db_love.hash_key, new_love.hash_key)

        with self.assertRaises(NoSuchLoveLink):
            loveapp.logic.love_link.get_love_link(old_love.hash_key)
