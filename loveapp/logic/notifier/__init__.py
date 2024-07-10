# -*- coding: utf-8 -*-
import loveapp.logic.event
from errors import UnknownEvent
from loveapp.logic.notifier.lovesent_notifier import LovesentNotifier


EVENT_TO_NOTIFIER_MAPPING = {
    loveapp.logic.event.LOVESENT: LovesentNotifier,
}


def notifier_for_event(event):
    try:
        return EVENT_TO_NOTIFIER_MAPPING[event]
    except KeyError:
        raise UnknownEvent('There is no such event as %s' % event)
