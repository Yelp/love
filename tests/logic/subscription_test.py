# -*- coding: utf-8 -*-
import mock
import unittest

import logic.subscription
from models import Subscription
from testing.factories import create_employee
from testing.factories import create_subscription


class SubscriptionTest(unittest.TestCase):
    nosegae_datastore_v3 = True

    @mock.patch('models.subscription.Employee', autospec=True)
    def test_delete_subscription(self, mock_model_employee):
        mock_model_employee.get_current_employee.return_value = create_employee()

        subscription = create_subscription()
        self.assertIsNotNone(Subscription.get_by_id(subscription.key.id()))

        logic.subscription.delete_subscription(subscription.key.id())

        self.assertIsNone(Subscription.get_by_id(subscription.key.id()))
