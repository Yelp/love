# -*- coding: utf-8 -*-

from models.employee import Employee


def get_all_departments():
    return sorted(
        [
            row.department
            for row in Employee.query(projection=['department'], distinct=True).fetch()
            if row.department
        ],
    )
