# -*- coding: utf-8 -*-
import binascii
import os

from flask import abort
from flask import request
from flask import session


def check_csrf_protection():
    """Make sure POST requests are sent with a CSRF token unless they're part of the API.
    In the future we might want to think about a system where we can disable CSRF protection
    on a per-view basis, maybe with a decorator.
    """
    if request.method == 'POST':
        token = session.get('_csrf_token')
        payload = request.form.get('_csrf_token')
        if not token or token != payload:
            abort(403)


def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = binascii.hexlify(os.urandom(16)).decode('ascii')
    return session['_csrf_token']
