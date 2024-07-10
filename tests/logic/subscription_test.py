# -*- coding: utf-8 -*-
import mock

import loveapp.logic.subscription
from loveapp.models import Subscription
from testing.factories import create_employee
from testing.factories import create_subscription


@mock.patch('loveapp.models.subscription.Employee', autospec=True)
def test_delete_subscription(mock_model_employee, gae_testbed):
    mock_model_employee.get_current_employee.return_value = create_employee()

    subscription = create_subscription()
    assert Subscription.get_by_id(subscription.key.id()) is not None

    loveapp.logic.subscription.delete_subscription(subscription.key.id())

    assert Subscription.get_by_id(subscription.key.id()) is None
