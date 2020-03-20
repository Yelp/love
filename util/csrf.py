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
        # request form of csrf token is returned as a string of a bytestring, slicing to just retrieve the bytestring
        # Not sure how else to do this :/
        byte_payload = bytes(payload[2:-1], encoding='ascii') if payload else None
        if not token or token != byte_payload:
            abort(403)


def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = binascii.hexlify(os.urandom(16))
    return session['_csrf_token']
