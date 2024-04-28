# -*- coding: utf-8 -*-
import itertools
import markupsafe
import re

import config


def get_company_value(value_id):
    return dict((value.id, value) for value in config.COMPANY_VALUES).get(value_id)


def get_company_value_link_pairs():
    value_link_pairs = [
        (value.display_string, '/value/' + value.id.lower())
        for value in config.COMPANY_VALUES
    ]
    return sorted(value_link_pairs)


def supported_hashtags():
    # Returns all supported hashtags
    return list(map(
        lambda x: '#' + x,
        itertools.chain(*[value.hashtags for value in config.COMPANY_VALUES])
    ))


def get_hashtag_value_mapping():
    hashtag_value_mapping = {}
    for value in config.COMPANY_VALUES:
        for hashtag in value.hashtags:
            hashtag_value_mapping['#' + hashtag.lower()] = value.id

    return hashtag_value_mapping


def linkify_company_values(love):
    # escape the input before we add our own safe links
    escaped_love = str(markupsafe.escape(love))
    hashtag_value_mapping = get_hashtag_value_mapping()

    # find all the hashtags.
    ht_regex = '#[a-zA-Z0-9]+'
    present_hashtags = re.findall(ht_regex, escaped_love)

    # find all the ones we care about
    valid_hashtags = set()
    for hashtag in present_hashtags:
        if hashtag.lower() in hashtag_value_mapping:
            valid_hashtags.add(hashtag)

    # replace the hashtags with urls
    for hashtag in valid_hashtags:
        value_anchor = '<a href="{value_url}">{word}</a>'.format(
            value_url='/value/' + hashtag_value_mapping[hashtag.lower()].lower(),
            word=hashtag
        )
        escaped_love = escaped_love.replace(hashtag, value_anchor)

    return markupsafe.Markup(escaped_love)


def values_matching_prefix(prefix):
    if prefix is None:
        return supported_hashtags()

    lower_prefix = prefix.lower()
    matching_hashtags = []
    for hashtag in supported_hashtags():
        if hashtag.lower().startswith(lower_prefix):
            matching_hashtags.append(hashtag)
    return matching_hashtags
