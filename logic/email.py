# -*- coding: utf-8 -*-

from util.email import get_name_and_email
import config
import logic.secret

from googleapiclient.discovery import build

from email.mime.text import MIMEText

import base64

from google.oauth2 import service_account
import json

if config.EMAIL_BACKEND == "sendgrid":
    # a bit of a hack here so that we can avoid adding dependencies unless
    # the user wants them
    import sendgrid

with open("service_account_credentials.json") as json_file:
    CREDS = json.loads(json_file.read())


def send_appengine_email(sender, recipient, subject, body_html, body_text):
    message = create_message(
        config.EMAIL_DELEGATION_ADDRESS, recipient, subject, body_html,
    )

    service = service_account_login()
    # me is the magic word to reference the account credentials
    send_message(service, "me", message)


def send_sendgrid_email(sender, recipient, subject, body_html, body_text):
    key = logic.secret.get_secret("SENDGRID_API_KEY")
    sg = sendgrid.SendGridAPIClient(apikey=key)

    from_ = sendgrid.helpers.mail.Email(*get_name_and_email(sender))
    to = sendgrid.helpers.mail.Email(*get_name_and_email(recipient))
    content_html = sendgrid.helpers.mail.Content("text/html", body_html)
    content_text = sendgrid.helpers.mail.Content("text/plain", body_text)
    # text/plain needs to be before text/html or sendgrid gets mad
    message = sendgrid.helpers.mail.Mail(from_, subject, to, content_text)
    message.add_content(content_html)

    sg.client.mail.send.post(request_body=message.get())


EMAIL_BACKENDS = {
    "appengine": send_appengine_email,
    "sendgrid": send_sendgrid_email,
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


def create_message(sender, to, subject, message_text):

    message = MIMEText(message_text, "html")
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject
    return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}


def send_message(service, user_id, message):
    # TODO try catch here

    service.users().messages().send(userId=user_id, body=message).execute()

    return message


# except errors.HttpError as error:
#     print()


def service_account_login():
    SCOPES = ["https://mail.google.com/"]
    SERVICE_ACCOUNT_FILE = "service_account_credentials.json"

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    delegated_credentials = credentials.with_subject(config.EMAIL_DELEGATION_ADDRESS)
    service = build("gmail", "v1", credentials=delegated_credentials)
    return service
