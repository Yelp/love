# -*- coding: utf-8 -*-
from models.subscription import Subscription


def delete_subscription(subscription_id):
    subscription = Subscription.get_by_id(subscription_id)
    subscription.key.delete()
