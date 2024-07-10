# -*- coding: utf-8 -*-
import json

from flask.helpers import make_response
from flask_themes2 import render_theme_template

import loveapp.config as config


def get_current_theme():
    return config.THEME


def make_json_response(data, *args):
    response = make_response(json.dumps(data), *args)
    response.headers['Content-Type'] = 'application/json'
    return response


def render_template(template, **context):
    return render_theme_template(get_current_theme(), template, **context)
