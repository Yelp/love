# -*- coding: utf-8 -*-
import mock

from testing.factories import create_love_link


@mock.patch('loveapp.models.love_link.config')
def test_url(mock_config):
    mock_config.APP_BASE_URL = 'http://foo.io/'

    link = create_love_link(hash_key='lOvEr')
    assert 'http://foo.io/l/lOvEr' == link.url
