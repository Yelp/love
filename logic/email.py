# -*- coding: utf-8 -*-
import re

from google.appengine.api.mail import EmailMessage

import config
import logic.secret

if config.EMAIL_BACKEND == 'sendgrid':
    # a bit of a hack here so that we can avoid adding dependencies unless
    # the user wants them
    import sendgrid


def get_name_and_email(email_string):
    """Take a string that is either 'Name <email>' or just an email address
    and return a two tuple (email, name). If there is just an email, returns
    None for the name."""
    match = re.match(r'(.*) <(.*)>', email_string)
    if match:
        return match.group(2), match.group(1)
    else:
        return email_string, None


def send_appengine_email(sender, recipient, subject, body_html, body_text):
    email = EmailMessage()
    email.sender = sender
    email.to = recipient
    email.subject = subject
    email.body = body_text
    email.html = body_html
    email.send()


def send_sendgrid_email(sender, recipient, subject, body_html, body_text):
    key = logic.secret.get_secret('SENDGRID_API_KEY')
    sg = sendgrid.SendGridAPIClient(apikey=key)

    from_ = sendgrid.helpers.mail.Email(*get_name_and_email(sender))
    to = sendgrid.helpers.mail.Email(*get_name_and_email(recipient))
    content_html = sendgrid.helpers.mail.Content('text/html', body_html)
    content_text = sendgrid.helpers.mail.Content('text/plain', body_text)
    # text/plain needs to be before text/html or sendgrid gets mad
    message = sendgrid.helpers.mail.Mail(from_, subject, to, content_text)
    message.add_content(content_html)

    sg.client.mail.send.post(request_body=message.get())


EMAIL_BACKENDS = {
    'appengine': send_appengine_email,
    'sendgrid': send_sendgrid_email,
}


def send_email(sender, recipient, subject, body_html, body_text):
    """Send an email using whatever configured backend there is.
    sender, recipient - email address, can be bare, or in the
        Name <address@example.com> format
    subject - string
    body_html - string
    body_text - string
    """
    backend = EMAIL_BACKENDS[config.EMAIL_BACKEND]
    backend(sender, recipient, subject, body_html, body_text)
