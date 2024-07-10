# -*- coding: utf-8 -*-
from loveapp.logic.employee import employees_matching_prefix
from loveapp.util.render import make_json_response


def autocomplete(request):
    """This is the implementation of the autocomplete API endpoint. It's shared between
    the api view and web view that is called from Javascript, only the authorization
    checks are different.
    """
    matches = employees_matching_prefix(request.args.get('term', None))
    users = [
        {
            'label': u'{} ({})'.format(full_name, username),
            'value': username,
            'avatar_url': photo_url,
        }
        for full_name, username, photo_url
        in matches
    ]
    return make_json_response(users)
