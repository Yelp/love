# -*- coding: utf-8 -*-
import unittest

import logic.alias

from models import Alias
from testing.factories import create_alias_with_employee_username
from testing.factories import create_employee


class TestAlias(unittest.TestCase):
    nosegae_datastore_v3 = True

    def test_get_alias(self):
        create_employee(username='fuz')
        create_alias_with_employee_username(name='fuzzi', username='fuz')

        assert logic.alias.get_alias('fuzzi') is not None

    def test_save_alias(self):
        johnd = create_employee(username='johnd')
        assert Alias.query().count() == 0

        alias = logic.alias.save_alias('johnny', 'johnd')

        assert Alias.query().count() == 1
        assert alias.name == 'johnny'
        assert alias.owner_key == johnd.key

    def test_delete_alias(self):
        create_employee(username='janed')
        alias = logic.alias.save_alias('jane', 'janed')
        assert Alias.query().count() == 1

        logic.alias.delete_alias(alias.key.id())

        assert Alias.query().count() == 0

    def test_name_for_alias_with_alias(self):
        create_employee(username='janed')
        logic.alias.save_alias('jane', 'janed')

        assert logic.alias.name_for_alias('jane') == 'janed'

    def test_name_for_alias_with_employee_name(self):
        assert logic.alias.name_for_alias('janed') == 'janed'
