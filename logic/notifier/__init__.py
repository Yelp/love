# -*- coding: utf-8 -*-
import logic.event

from errors import UnknownEvent
from logic.notifier.lovesent_notifier import LovesentNotifier


EVENT_TO_NOTIFIER_MAPPING = {
    logic.event.LOVESENT: LovesentNotifier,
}


def notifier_for_event(event):
    try:
        return EVENT_TO_NOTIFIER_MAPPING[event]
    except KeyError:
        raise UnknownEvent('There is no such event as %s' % event)
