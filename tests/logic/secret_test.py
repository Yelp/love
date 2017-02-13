# -*- coding: utf-8 -*-
import unittest

from errors import NoSuchSecret
from logic.secret import get_secret
from testing.factories import create_secret


class SecretTest(unittest.TestCase):
    nosegae_datastore_v3 = True

    def test_existing_secret(self):
        create_secret('FOO', value='bar')
        self.assertEqual('bar', get_secret('FOO'))

    def test_unknown_secret(self):
        with self.assertRaises(NoSuchSecret):
            get_secret('THANKS_FOR_ALL_THE_FISH')
