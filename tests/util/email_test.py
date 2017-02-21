# -*- coding: utf-8 -*-
import unittest

import util.email


class GetNameAndEmailTest(unittest.TestCase):
    """Tests util.email.get_name_and_email()"""

    def test_bare_email(self):
        email_string = 'darwin@example.com'
        email, name = util.email.get_name_and_email(email_string)
        self.assertEqual(email, email_string)
        self.assertIsNone(name)

    def test_name_and_email(self):
        email_string = 'Darwin Stoppelman <darwin@example.com>'
        email, name = util.email.get_name_and_email(email_string)
        self.assertEqual(email, 'darwin@example.com')
        self.assertEqual(name, 'Darwin Stoppelman')
