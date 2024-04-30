# -*- coding: utf-8 -*-
import unittest

import mock
import pytest

import loveapp.logic.email


@pytest.mark.usefixtures('gae_testbed')
class EmailTest(unittest.TestCase):
    """We really just want to test that configuration is honored here."""

    sender = 'test@example.com'
    recipient = 'test@example.com'
    subject = 'test subject'
    html = '<p>hello test</p>'
    text = 'hello test'

    @mock.patch('loveapp.logic.email.EMAIL_BACKENDS')
    @mock.patch('loveapp.logic.email.config')
    def test_send_email_appengine(self, mock_config, mock_backends):
        mock_config.EMAIL_BACKEND = 'appengine'
        mock_backends['appengine'] = mock.Mock()
        loveapp.logic.email.send_email(self.sender, self.recipient, self.subject,
                                       self.html, self.text)
        mock_backends['appengine'].assert_called_once_with(
            self.sender, self.recipient, self.subject, self.html, self.text
        )

    @mock.patch('loveapp.logic.email.EMAIL_BACKENDS')
    @mock.patch('loveapp.logic.email.config')
    def test_send_email_sendgrid(self, mock_config, mock_backends):
        mock_config.EMAIL_BACKEND = 'sendgrid'
        mock_backends['sendgrid'] = mock.Mock()
        loveapp.logic.email.send_email(self.sender, self.recipient, self.subject,
                                       self.html, self.text)
        mock_backends['sendgrid'].assert_called_once_with(
            self.sender, self.recipient, self.subject, self.html, self.text
        )
