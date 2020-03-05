# -*- coding: utf-8 -*-
# flake8: noqa
from flask import Flask

from flask_themes2 import Themes
from flask_oidc import OpenIDConnect
import config
from util.converter import RegexConverter
from util.csrf import generate_csrf_token
from google.cloud import ndb


client = ndb.Client()


def ndb_wsgi_middleware(wsgi_app):
    def middleware(environ, start_response):
        with client.context():
            return wsgi_app(environ, start_response)

    return middleware


app = Flask(__name__.split(".")[0])
app.wsgi_app = ndb_wsgi_middleware(app.wsgi_app)  # Wrap the app in middleware.
app.secret_key = config.SECRET_KEY
app.url_map.converters["regex"] = RegexConverter
app.jinja_env.globals["config"] = config
app.jinja_env.globals["csrf_token"] = generate_csrf_token
app.config["OIDC_CLIENT_SECRETS"] = "client_secrets.json"
app.config["OIDC_COOKIE_SECURE"] = not config.DEBUG
app.config["OIDC_CALLBACK_ROUTE"] = "/oidc_callback"
app.config["OIDC_SCOPES"] = ["openid", "email", "groups"]
app.config["SECRET_KEY"] = config.SECRET_KEY
oidc = OpenIDConnect(app,)
Themes(app, app_identifier="yelplove")

# if debug property is present, let's use it
try:
    app.debug = config.DEBUG
except AttributeError:
    app.debug = False

# This import needs to stay down here, otherwise we'll get ImportErrors when running tests
import views  # noqa
