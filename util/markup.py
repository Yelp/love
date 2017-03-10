# -*- coding: utf-8 -*-
from dominate.tags import a
from flask import url_for


def explore_links(employees, app_context):
    with app_context:
        return [
            a(employee, href=url_for('explore', user=employee)).render()
            for employee in employees
        ]
