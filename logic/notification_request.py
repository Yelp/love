# -*- coding: utf-8 -*-
import hashlib
import hmac
import json
import logging
import urllib3

import config


CONTENT_TYPE_JSON = 'application/json'


pool = urllib3.PoolManager()


class NotificationRequest(object):

    def __init__(self, subscription, payload):
        self.url = subscription.request_url
        self.method = subscription.request_method
        self.format = subscription.request_format
        self.secret = subscription.secret
        self.event = subscription.event
        self.content = self._content(self.format, payload)

    def send(self):
        try:
            return pool.urlopen(
                self.method,
                self.url,
                body=self.content.payload,
                headers=self.headers,
            )
        except Exception:
            logging.info('Could not send request to %s', self.url)
            return False

    @property
    def headers(self):
        # hmac does not like unicode
        digest = hmac.new(str(self.secret), str(self.content.payload), hashlib.sha1)
        return {
            'Content-type': self.content.content_type,
            'X-YelpLove-Event': self.event,
            'User-Agent': '{} ({})'.format(config.APP_NAME, config.APP_BASE_URL),
            'X-Hub-Signature': digest.hexdigest(),
        }

    def _content(self, format, payload):
        if CONTENT_TYPE_JSON == format:
            return JSONContent(payload)
        else:
            raise RuntimeError('Unsupported format %s' % format)


class JSONContent(object):
    def __init__(self, payload):
        self.content_type = CONTENT_TYPE_JSON
        self.payload = json.dumps(payload)
