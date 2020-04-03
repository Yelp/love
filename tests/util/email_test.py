# -*- coding: utf-8 -*-
import unittest

import util.email


class TestGetNameAndEmail(unittest.TestCase):
    """Tests util.email.get_name_and_email()"""

    def test_bare_email(self):
        email_string = 'darwin@example.com'
        email, name = util.email.get_name_and_email(email_string)
        assert email == email_string
        assert name is None

    def test_name_and_email(self):
        email_string = 'Darwin Stoppelman <darwin@example.com>'
        email, name = util.email.get_name_and_email(email_string)
        assert email == 'darwin@example.com'
        assert name == 'Darwin Stoppelman'
