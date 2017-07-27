# -*- coding: utf-8 -*-


class InvalidToggleName(Exception):
    pass


class InvalidToggleState(Exception):
    pass


class NoSuchEmployee(Exception):
    pass


class NoSuchSecret(Exception):
    pass


class UnknownEvent(Exception):
    pass


class NoSuchLoveLink(Exception):
    pass

class TaintedLove(Exception):

    def __init__(self, user_message, is_error=True):
        self.user_message = user_message
        self.is_error = (is_error is True)
