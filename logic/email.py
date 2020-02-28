# -*- coding: utf-8 -*-
# from google.appengine.api.mail import EmailMessage

from util.email import get_name_and_email
import config
import logic.secret
import requests
from google.auth import jwt
from google.auth import crypt
import time

# import os
from googleapiclient.discovery import build

# from apiclient import errors
from email.mime.text import MIMEText

# from email.mime.multipart import MIMEMultipart
import base64

# from oauth2client import file, client, tools
# from httplib2 import Http
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


def createGoogleHeaders():
    for attempt in range(5):
        jwtClaimSet = {
            "iss": config.EMAIL_SERVICE_ACCOUNT,
            "sub": config.EMAIL_DELEGATION_ADDRESS,
            "scope": "https://mail.google.com/",
            "aud": "https://oauth2.googleapis.com/token",
            "exp": int(time.time() + 3600),
            "iat": int(time.time()),
        }
        signer = crypt.RSASigner.from_service_account_info(CREDS)
        token = jwt.encode(signer, jwtClaimSet)
        data = {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": token,
        }
        try:
            response = requests.post(
                "https://oauth2.googleapis.com/token", data=data
            ).json()
        except requests.RequestException:
            continue
        if response.get("access_token"):
            headers = {
                "Authorization": f"Bearer {response['access_token']}",
            }
            return headers
        else:
            continue
    return None
