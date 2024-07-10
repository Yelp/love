# -*- coding: utf-8 -*-
import unittest

import pytest

from errors import NoSuchSecret
from loveapp.logic.secret import get_secret
from testing.factories import create_secret


@pytest.mark.usefixtures('gae_testbed')
class SecretTest(unittest.TestCase):

    def test_existing_secret(self):
        create_secret('FOO', value='bar')
        self.assertEqual('bar', get_secret('FOO'))

    def test_unknown_secret(self):
        with self.assertRaises(NoSuchSecret):
            get_secret('THANKS_FOR_ALL_THE_FISH')
