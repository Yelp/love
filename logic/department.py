# -*- coding: utf-8 -*-

import yaml


_departments = yaml.safe_load(open('departments.yaml'))

META_DEPARTMENTS = set(_departments.keys())

DEFAULT_META_DEPARTMENT = 'Other'

assert DEFAULT_META_DEPARTMENT in META_DEPARTMENTS

META_DEPARTMENT_MAP = {
    meta_department: set(departments)
    for meta_department, departments in _departments.items()
}


def get_meta_department(dept):
    for meta_dept, dept_set in META_DEPARTMENT_MAP.items():
        if dept in dept_set:
            return meta_dept
    return DEFAULT_META_DEPARTMENT
