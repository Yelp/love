# -*- coding: utf-8 -*-
# flake8: noqa
from flask import Flask
from flask_themes2 import Themes

import config
from util.auth import is_admin
from util.converter import RegexConverter
from util.company_values import linkify_company_values
from util.csrf import generate_csrf_token


app = Flask(__name__.split('.')[0])
app.secret_key = config.SECRET_KEY
app.url_map.converters['regex'] = RegexConverter
app.jinja_env.globals['config'] = config
app.jinja_env.globals['csrf_token'] = generate_csrf_token
app.jinja_env.globals['is_admin'] = is_admin
app.jinja_env.filters['linkify_company_values'] = linkify_company_values

Themes(app, app_identifier='yelplove')

# if debug property is present, let's use it
try:
    app.debug = config.DEBUG
except AttributeError:
    app.debug = False

# This import needs to stay down here, otherwise we'll get ImportErrors when running tests
import views  # noqa
