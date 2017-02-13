# -*- coding: utf-8 -*-
from errors import NoSuchSecret
from models import Secret


def get_secret(id):
    secret = Secret.get_by_id(id)
    if secret:
        return secret.value
    else:
        raise NoSuchSecret(id)
