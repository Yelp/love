# -*- coding: utf-8 -*-
from models.employee import Employee


def get_all_offices():
    return [
        row.office
        for row in Employee.query(projection=['office'], distinct=True).fetch()
        if row.office
    ]


def get_all_offices_compressed():
    """
    Some random offices data we have:
        - Canada: Remote
        - Canada: Toronto Office
        - Czech Republic: Remote
        - Germany: Hamburg Office
        - USA: NY Fifth Ave Office
        - USA: NY Madison Ave Office
        - USA: CA SF Remote
        - United Kingdom: London Office
        - United Kingdom: Remote
        - USA: CA SF Hawthorne Office
        - USA: CA SF New Montgomery Office
    The goal is to group them according to the location. So the final output should be
        - Canada
        - Czech Republic
        - Germany Hamburg
        - USA NY
        - United Kingdom
        - USA CA
    """
    offices = sorted(
        [
            office.replace(' Remote', '').replace(' Office', '')
            for office in get_all_offices()
        ],
        reverse=True,
    )
    return get_compressed_list(offices)


def get_compressed_list(x):
    """
        Sample Input: [
            'United Kingdom London',
            'United Kingdom',
            'USA NY Madison Ave',
            'USA NY Fifth Ave',
            'USA CA SF New Montgomery',
            'USA CA SF Hawthorne',
            'USA CA SF',
            'Germany Hamburg',
            'Czech Republic',
            'Canada Toronto',
            'Canada',
        ]

        Sample Output: set([
            'Canada',
            'United Kingdom',
            'USA NY Madison Ave',
            'Germany Hamburg',
            'USA NY Fifth Ave',
            'USA CA SF',
            'Czech Republic',
        ])
    """
    if len(x) == 0:
        return set([])
    item = x.pop().split(' ')
    result = set()
    while len(x) > 0:
        item_to_match = x.pop().split(' ')
        intersection = set(item) & set(item_to_match)
        if len(intersection) != len(item):
            result.add(' '.join(item))
            item = item_to_match
    result.add(' '.join(item))
    return result
