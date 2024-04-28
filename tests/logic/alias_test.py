# -*- coding: utf-8 -*-
import unittest

import loveapp.logic.alias

from loveapp.models import Alias
from testing.factories import create_alias_with_employee_username
from testing.factories import create_employee


class AliasTest(unittest.TestCase):
    nosegae_datastore_v3 = True

    def test_get_alias(self):
        create_employee(username='fuz')
        create_alias_with_employee_username(name='fuzzi', username='fuz')

        self.assertIsNotNone(loveapp.logic.alias.get_alias('fuzzi'))

    def test_save_alias(self):
        johnd = create_employee(username='johnd')
        self.assertEqual(Alias.query().count(), 0)

        alias = loveapp.logic.alias.save_alias('johnny', 'johnd')

        self.assertEqual(Alias.query().count(), 1)
        self.assertEqual(alias.name, 'johnny')
        self.assertEqual(alias.owner_key, johnd.key)

    def test_delete_alias(self):
        create_employee(username='janed')
        alias = loveapp.logic.alias.save_alias('jane', 'janed')
        self.assertEqual(Alias.query().count(), 1)

        loveapp.logic.alias.delete_alias(alias.key.id())

        self.assertEqual(Alias.query().count(), 0)

    def test_name_for_alias_with_alias(self):
        create_employee(username='janed')
        loveapp.logic.alias.save_alias('jane', 'janed')

        self.assertEqual(loveapp.logic.alias.name_for_alias('jane'), 'janed')

    def test_name_for_alias_with_employee_name(self):
        self.assertEqual(loveapp.logic.alias.name_for_alias('janed'), 'janed')
