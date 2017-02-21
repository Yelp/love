# -*- coding: utf-8 -*-
import re


def get_name_and_email(email_string):
    """Take a string that is either 'Name <email>' or just an email address
    and return a two tuple (email, name). If there is just an email, returns
    None for the name."""
    match = re.match(r'(.*) <(.*)>', email_string)
    if match:
        return match.group(2), match.group(1)
    else:
        return email_string, None
