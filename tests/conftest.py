# -*- coding: utf-8 -*-
import pytest

from loveapp import create_app


@pytest.fixture(autouse=True)
def app():  # noqa

    app = create_app()

    with app.app_context():
        yield app
