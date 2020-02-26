# -*- coding: utf-8 -*-
from functools import wraps

from flask import abort

# from flask import redirect
from flask import request

# from flask import session
from flask.helpers import make_response
from main import oidc

# from google.appengine.api import users

from models.access_key import AccessKey
from util.csrf import check_csrf_protection


# def user_required(func):
#     @wraps(func)
#     def decorated_view(*args, **kwargs):
#         if not users.get_current_user():
#             return redirect(users.create_login_url(request.url))
#         return func(*args, **kwargs)

#     return decorated_view


def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        # x = oidc
        # y = (oidc.user_getfield('email'))
        # z = oidc.user_getfield('groups')
        # s = session
        if "Access-Love-Admin" not in oidc.user_getfield("groups"):
            abort(401)  # Unauthorized
        return func(*args, **kwargs)

    return decorated_view


def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.form.get("api_key") or request.args.get("api_key")
        valid_api_key = False
        if api_key is not None:
            valid_api_key = (
                AccessKey.query(AccessKey.access_key == api_key).get(keys_only=True)
                is not None
            )
        if not valid_api_key:
            return make_response(
                "Invalid API Key",
                401,
                {"WWWAuthenticate": 'Basic realm="Login Required"'},
            )
        return f(*args, **kwargs)

    return decorated_function


def csrf_protect(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        check_csrf_protection()
        return func(*args, **kwargs)

    return decorated_view
