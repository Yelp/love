# -*- coding: utf-8 -*-
from collections import namedtuple


PaginationResult = namedtuple(
    "PaginationResult", ["collection", "prev_offset", "next_offset", "prev", "next"],
)


class Pagination(object):
    ITEMS_PER_PAGE = 20

    @classmethod
    def paginate(cls, order_by, offset):
        offset = 0 if offset is None or int(offset) < 0 else int(offset)
        objects = (
            cls.query()
            .order(order_by)
            .fetch(offset=int(offset), limit=cls.ITEMS_PER_PAGE)
        )
        prev = False if offset == 0 else True

        next_ = True if len(objects) == cls.ITEMS_PER_PAGE else False

        return PaginationResult(
            collection=objects,
            prev_offset=offset - cls.ITEMS_PER_PAGE,
            next_offset=offset + cls.ITEMS_PER_PAGE,
            prev=prev,
            next=next_,
        )

    # @classmethod
    # def paginate(cls, order_by, prev_cursor_str, next_cursor_str):
    #     if not prev_cursor_str and not next_cursor_str:
    #         objects, next_cursor, more = (
    #             cls.query().order(order_by).fetch_page(cls.ITEMS_PER_PAGE)
    #         )
    #         prev_cursor_str = ""
    #         if next_cursor:
    #             next_cursor_str = next_cursor.urlsafe()
    #         else:
    #             next_cursor_str = ""
    #         next_ = True if more else False
    #         prev = False
    #     elif next_cursor_str:
    #         # cursor = Cursor(urlsafe=next_cursor_str)
    #         objects, next_cursor, more = (
    #             cls.query()
    #             .order(order_by)
    #             .fetch(limit=cls.ITEMS_PER_PAGE, start_cursor=next_cursor_str,)
    #         )
    #         prev_cursor_str = next_cursor_str
    #         next_cursor_str = next_cursor.urlsafe()
    #         prev = True
    #         next_ = True if more else False
    #     elif prev_cursor_str:
    #         cursor = Cursor(urlsafe=prev_cursor_str)
    #         objects, next_cursor, more = (
    #             cls.query()
    #             .order(-order_by)
    #             .fetch_page(cls.ITEMS_PER_PAGE, start_cursor=cursor,)
    #         )
    #         objects.reverse()
    #         next_cursor_str = prev_cursor_str
    #         prev_cursor_str = next_cursor.urlsafe()
    #         prev = True if more else False
    #         next_ = True

    #     return PaginationResult(
    #         collection=objects,
    #         prev_cursor=prev_cursor_str,
    #         next_cursor=next_cursor_str,
    #         prev=prev,
    #         next=next_,
    #     )
