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
