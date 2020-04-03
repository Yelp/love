# -*- coding: utf-8 -*-
import mock
import unittest

from testing.factories import create_love_link


class TestLoveLink(unittest.TestCase):
    # enable the datastore stub
    nosegae_datastore_v3 = True

    @mock.patch('models.love_link.config')
    def test_url(self, mock_config):
        mock_config.APP_BASE_URL = 'http://foo.io/'

        link = create_love_link(hash_key='lOvEr')
        assert 'http://foo.io/l/lOvEr' == link.url
