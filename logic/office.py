# -*- coding: utf-8 -*-
from models import Employee


def get_all_offices():
    """
    Retrieve all the offices in the database
    Returns: List[str]
    """
    return [
        row.office
        for row in Employee.query(projection=['office'], distinct=True).fetch()
        if row.office
    ]
