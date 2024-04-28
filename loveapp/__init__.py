# -*- coding: utf-8 -*-

from google.appengine.api import wrap_wsgi_app
from flask import Flask
from flask_themes2 import Themes

import loveapp.config as config
from loveapp.util.auth import is_admin
from loveapp.util.converter import RegexConverter
from loveapp.util.company_values import linkify_company_values
from loveapp.util.csrf import generate_csrf_token

from loveapp import views


def create_app():
    app = Flask(__name__.split('.')[0])
    app.wsgi_app = wrap_wsgi_app(app.wsgi_app)

    app.secret_key = config.SECRET_KEY
    app.url_map.converters['regex'] = RegexConverter
    app.jinja_env.globals['config'] = config
    app.jinja_env.globals['csrf_token'] = generate_csrf_token
    app.jinja_env.globals['is_admin'] = is_admin
    app.jinja_env.filters['linkify_company_values'] = linkify_company_values

    app.register_blueprint(views.web.web_app)
    app.register_blueprint(views.api.api_app)
    app.register_blueprint(views.tasks.tasks_app)

    Themes(app, app_identifier='yelplove')

    # if debug property is present, let's use it
    try:
        app.debug = config.DEBUG
    except AttributeError:
        app.debug = False

    return app
