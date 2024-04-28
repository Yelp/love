# -*- coding: utf-8 -*-
from loveapp.models import LoveLink


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

    return new_love_link
