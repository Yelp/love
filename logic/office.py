# -*- coding: utf-8 -*-
import yaml


OFFICES = yaml.safe_load(open('offices.yaml'))
REMOTE_OFFICE = 'Remote'
OTHER_OFFICE = 'Other'


def get_all_offices():
    from models import Employee

    """
    Retrieve all the offices in the database
    Returns: List[str]
    """
    return [
        row.office
        for row in Employee.query(projection=['office'], distinct=True).fetch() if row.office
    ]


def get_office_name(employee_office_location):
    """
    Given the employee office location retrieve the office name
    The matching is done by basic string matching
    Args:
        employee_office_location: str
        Returns: str

    Examples in: out
        if we have yaml file with the follwong content: {Hamburg office, SF office}
        NY Remote: Remote
        SF office: SF office
        SF office Remote: SF office
        Germany Hamburg office: Hamburg office
        CA SF New Montgomery Office: Sf office
    """
    employee_office_location = employee_office_location.lower()

    for office in OFFICES:
        if office.lower() in employee_office_location:
            return office

    if REMOTE_OFFICE.lower() in employee_office_location:
        return REMOTE_OFFICE

    return OTHER_OFFICE
