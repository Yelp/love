# -*- coding: utf-8 -*-
from time import sleep

from errors import InvalidToggleName
from errors import InvalidToggleState
from models import Toggle
from models.toggle import TOGGLE_NAMES
from models.toggle import TOGGLE_STATES


def _validate_and_maybe_create_toggle(name, state):
    if name not in TOGGLE_NAMES:
        raise InvalidToggleName(name)
    if state not in TOGGLE_STATES:
        raise InvalidToggleState(str(state))

    toggle = Toggle.query(Toggle.name == name).get()
    if toggle is None:
        toggle = Toggle(name=name, state=state)
        toggle.put()
    return toggle


def get_toggle_state(name, default=True):
    toggle = _validate_and_maybe_create_toggle(name, default)
    return toggle.state


def set_toggle_state(name, state):
    toggle = _validate_and_maybe_create_toggle(name, state)
    if toggle.state != state:
        toggle.state = state
        toggle.put()

    # It hurts me to have to do this, but the datastore is eventually consistent so...
    key = toggle.key
    while True:
        sleep(2)
        toggle = key.get()
        if toggle.state == state:
            break
