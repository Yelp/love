# -*- coding: utf-8 -*-
from loveapp.models.access_key import AccessKey


def test_create(gae_testbed):
    key = AccessKey.create('description')

    assert key is not None
    assert 'description' == key.description
    assert key.access_key is not None
