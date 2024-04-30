# -*- coding: utf-8 -*-
import unittest

import mock

import loveapp.util.company_values
from loveapp.config import CompanyValue


class CompanyValuesUtilTest(unittest.TestCase):

    COMPANY_VALUE_ONE = CompanyValue('FAKE_VALUE_ONE', 'Fake Value 1', ['fakevalue1'])
    COMPANY_VALUE_TWO = CompanyValue('FAKE_VALUE_TWO', 'Fake Value 2', ['fakevalue2', 'otherhashtag'])

    @mock.patch('loveapp.util.company_values.config')
    def test_get_company_value(self, mock_config):
        mock_config.COMPANY_VALUES = [
            self.COMPANY_VALUE_ONE,
            self.COMPANY_VALUE_TWO
        ]
        company_value = loveapp.util.company_values.get_company_value(self.COMPANY_VALUE_ONE.id)
        self.assertEqual(company_value, self.COMPANY_VALUE_ONE)

        probably_None = loveapp.util.company_values.get_company_value('fake_value')
        self.assertEqual(None, probably_None)

    @mock.patch('loveapp.util.company_values.config')
    def test_supported_hashtags(self, mock_config):
        mock_config.COMPANY_VALUES = []
        supported_hashtags = loveapp.util.company_values.supported_hashtags()
        self.assertEqual(supported_hashtags, [])

        mock_config.COMPANY_VALUES = [self.COMPANY_VALUE_TWO]
        supported_hashtags = loveapp.util.company_values.supported_hashtags()
        self.assertEqual(supported_hashtags, ['#fakevalue2', '#otherhashtag'])

    @mock.patch('loveapp.util.company_values.config')
    def test_get_hashtag_value_mapping(self, mock_config):
        mock_config.COMPANY_VALUES = []
        hashtag_mapping = loveapp.util.company_values.get_hashtag_value_mapping()
        self.assertEqual({}, hashtag_mapping)

        mock_config.COMPANY_VALUES = [
            self.COMPANY_VALUE_ONE,
            self.COMPANY_VALUE_TWO
        ]

        expected_mapping = {
            '#' + self.COMPANY_VALUE_ONE.hashtags[0]: self.COMPANY_VALUE_ONE.id,
            '#' + self.COMPANY_VALUE_TWO.hashtags[0]: self.COMPANY_VALUE_TWO.id,
            '#' + self.COMPANY_VALUE_TWO.hashtags[1]: self.COMPANY_VALUE_TWO.id,
        }
        hashtag_mapping = loveapp.util.company_values.get_hashtag_value_mapping()
        self.assertEqual(expected_mapping, hashtag_mapping)

    @mock.patch('loveapp.util.company_values.config')
    def test_linkify_company_values(self, mock_config):
        mock_config.COMPANY_VALUES = []
        love_text = u'who wants to #liveForever? 😭'
        linkified_value = loveapp.util.company_values.linkify_company_values(love_text)
        # should be the same, because there's no hashtags.
        self.assertEqual(love_text, linkified_value)

        mock_config.COMPANY_VALUES = [
            CompanyValue('FREDDIE', 'Mercury', ('liveForever',))
        ]
        love_text = 'who wants to #liveForever?'
        linkified_value = loveapp.util.company_values.linkify_company_values(love_text)
        # there should be a link in here now
        self.assertIn('href', linkified_value)

    @mock.patch('loveapp.util.company_values.config')
    def test_values_matching_prefix(self, mock_config):
        mock_config.COMPANY_VALUES = [
            CompanyValue('TEST', 'test', ['abseil', 'absolute', 'abrasion'])
        ]

        self.assertEqual(
            set(['#abseil', '#absolute', '#abrasion']),
            set(loveapp.util.company_values.values_matching_prefix('#a'))
        )

        self.assertEqual(
            set(['#abseil', '#absolute']),
            set(loveapp.util.company_values.values_matching_prefix('#abs'))
        )
