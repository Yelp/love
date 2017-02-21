# -*- coding: utf-8 -*-
from collections import namedtuple

from google.appengine.datastore.datastore_query import Cursor


PaginationResult = namedtuple(
    'PaginationResult',
    [
        'collection',
        'prev_cursor',
        'next_cursor',
        'prev',
        'next',
    ],
)


class Pagination(object):
    ITEMS_PER_PAGE = 20

    @classmethod
    def paginate(cls, order_by, prev_cursor_str, next_cursor_str):
        if not prev_cursor_str and not next_cursor_str:
            objects, next_cursor, more = cls.query().order(order_by).fetch_page(cls.ITEMS_PER_PAGE)
            prev_cursor_str = ''
            if next_cursor:
                next_cursor_str = next_cursor.urlsafe()
            else:
                next_cursor_str = ''
            next_ = True if more else False
            prev = False
        elif next_cursor_str:
            cursor = Cursor(urlsafe=next_cursor_str)
            objects, next_cursor, more = cls.query().order(order_by).fetch_page(
                cls.ITEMS_PER_PAGE,
                start_cursor=cursor,
            )
            prev_cursor_str = next_cursor_str
            next_cursor_str = next_cursor.urlsafe()
            prev = True
            next_ = True if more else False
        elif prev_cursor_str:
            cursor = Cursor(urlsafe=prev_cursor_str)
            objects, next_cursor, more = cls.query().order(-order_by).fetch_page(
                cls.ITEMS_PER_PAGE,
                start_cursor=cursor,
            )
            objects.reverse()
            next_cursor_str = prev_cursor_str
            prev_cursor_str = next_cursor.urlsafe()
            prev = True if more else False
            next_ = True

        return PaginationResult(
            collection=objects,
            prev_cursor=prev_cursor_str,
            next_cursor=next_cursor_str,
            prev=prev,
            next=next_,
        )
