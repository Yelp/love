# -*- coding: utf-8 -*-
import unittest

from testing.util import get_test_app
from util.markup import explore_links


class ExploreLinksTest(unittest.TestCase):
    """Tests util.email.explore_links()"""

    def setUp(self):
        self.app = get_test_app().app
        self.app.config.update(SERVER_NAME='foo.com')
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app.config.update(SERVER_NAME=None)
        self.app_context.pop()

    def test_empty_list(self):
        self.assertEqual(explore_links([], self.app_context), [])

    def test_explore_links(self):
        links = explore_links(['darwin'], self.app_context)
        self.assertEqual(links, ['<a href="http://foo.com/explore?user=darwin">darwin</a>'])
