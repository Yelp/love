# -*- coding: utf-8 -*-
from loveapp.models import Secret


def create_secret(id, value='secret'):
    secret = Secret(id=id, value=value)
    secret.put()
    return secret
