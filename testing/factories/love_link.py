# -*- coding: utf-8 -*-
from models import LoveLink


def create_love_link(
    hash_key='lOvEr',
    message='I <3 love links',
    recipient_list='johndoe, janedoe',
):

    new_love_link = LoveLink(
        hash_key=hash_key,
        message=message,
        recipient_list=recipient_list,
    )
    new_love_link.put()

    return new_love_link
