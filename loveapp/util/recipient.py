# -*- coding: utf-8 -*-


def sanitize_recipients(recipient_str):
    recipients = recipient_str.split(',')
    recipients = [
        recipient.lower().strip() for recipient in recipients
        if recipient.lower().strip()
    ]
    recipients = set(recipients)
    return recipients
