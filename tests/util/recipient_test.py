# -*- coding: utf-8 -*-
import unittest

from util.recipient import sanitize_recipients


class SanitizeRecipientsTest(unittest.TestCase):
    def _test_sanitization(self, input_recipients, expected_recipients):
        sanitized_recipients = sanitize_recipients(input_recipients)
        self.assertEqual(
            sanitized_recipients,
            expected_recipients,
        )

    def test_one_recipient(self):
        self._test_sanitization(
            'wwu',
            set(['wwu']),
        )

    def test_comma_separated_recipients(self):
        self._test_sanitization(
            'wwu,Basher,AMFONTS,yoann',
            set(['wwu', 'basher', 'amfonts', 'yoann']),
        )

    def test_comma_space_sparated_recipients(self):
        self._test_sanitization(
            'wwu, Basher, AMFONTS, yoann',
            set(['wwu', 'basher', 'amfonts', 'yoann']),
        )
