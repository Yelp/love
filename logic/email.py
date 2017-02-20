# -*- coding: utf-8 -*-
from google.appengine.api.mail import EmailMessage

import config


def send_appengine_email(sender, recipient, subject, body_html, body_text):
    email = EmailMessage()
    email.sender = sender
    email.to = recipient
    email.subject = subject
    email.body = body_text
    email.html = body_html
    email.send()


EMAIL_BACKENDS = {
    'appengine': send_appengine_email,
}


def send_email(sender, recipient, subject, body_html, body_text):
    """Send an email notifying the recipient of l about their love."""
    backend = EMAIL_BACKENDS[config.EMAIL_BACKEND]
    backend(sender, recipient, subject, body_html, body_text)
