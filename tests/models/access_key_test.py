# -*- coding: utf-8 -*-
import unittest

from models.access_key import AccessKey


class TestAccessKey(unittest.TestCase):
    # enable the datastore stub
    nosegae_datastore_v3 = True

    def test_create(self):
        key = AccessKey.create('description')

        assert key is not None
        assert 'description' == key.description
        assert key.access_key is not None
