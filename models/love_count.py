# -*- coding: utf-8 -*-
from google.appengine.ext import ndb

from logic import utc_week_limits


class LoveCount(ndb.Model):
    received_count = ndb.IntegerProperty(default=0)
    sent_count = ndb.IntegerProperty(default=0)
    week_start = ndb.DateTimeProperty()
    meta_department = ndb.StringProperty()
    department = ndb.StringProperty()

    @classmethod
    def update(cls, love, employee_dict=None):
        utc_week_start, _ = utc_week_limits(love.timestamp)

        sender_count = cls.query(
            ancestor=love.sender_key,
            filters=(cls.week_start == utc_week_start)
        ).get()
        if sender_count is not None:
            sender_count.sent_count += 1
        else:
            employee = employee_dict[love.sender_key] if employee_dict else love.sender_key.get()
            sender_count = cls(
                parent=love.sender_key,
                sent_count=1,
                week_start=utc_week_start,
                department=employee.department,
                meta_department=employee.meta_department,
            )
        sender_count.put()

        recipient_count = cls.query(
            ancestor=love.recipient_key,
            filters=(cls.week_start == utc_week_start)
        ).get()
        if recipient_count is not None:
            recipient_count.received_count += 1
        else:
            employee = employee_dict[love.recipient_key] if employee_dict else love.recipient_key.get()
            recipient_count = cls(
                parent=love.recipient_key,
                received_count=1,
                week_start=utc_week_start,
                department=employee.department,
                meta_department=employee.meta_department,
            )
        recipient_count.put()

    @classmethod
    def remove(cls, love):
        utc_week_start, _ = utc_week_limits(love.timestamp)

        sender_count = cls.query(
            ancestor=love.sender_key,
            filters=(cls.week_start == utc_week_start)
        ).get()
        if sender_count is not None and sender_count.sent_count > 0:
            sender_count.sent_count -= 1
            if sender_count.sent_count == 0 and sender_count.received_count == 0:
                sender_count.key.delete()
            else:
                sender_count.put()

        recipient_count = cls.query(
            ancestor=love.recipient_key,
            filters=(cls.week_start == utc_week_start)
        ).get()
        if recipient_count is not None and recipient_count.received_count > 0:
            recipient_count.received_count -= 1
            if recipient_count.sent_count == 0 and recipient_count.received_count == 0:
                recipient_count.key.delete()
            else:
                recipient_count.put()
