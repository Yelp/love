# -*- coding: utf-8 -*-
import unittest

from loveapp.models.access_key import AccessKey


class AccessKeyTest(unittest.TestCase):
    # enable the datastore stub
    nosegae_datastore_v3 = True

    def test_create(self):
        key = AccessKey.create('description')

        self.assertIsNotNone(key)
        self.assertEqual('description', key.description)
        self.assertIsNotNone(key.access_key)
