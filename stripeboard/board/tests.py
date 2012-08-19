import json

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase


from stripeboard.board.utils import (retrieve_paying_customers,
                                     retrieve_subscription_end_events,
                                     epoch_utc)


class StripeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        self.profile = self.user.get_profile()
        self.profile.stripe_api_key = settings.STRIPE_TEST_API_KEY
        self.profile.save()

        # cache.clear()

    # def test_stripe_customers(self):
    #     customers = retrieve_paying_customers(self.profile.stripe_api_key)
    #     print len(customers)

    # def test_stripe_events(self):
    #     events = retrieve_subscription_end_events(self.profile.stripe_api_key)
    #     print len(events)

    def test_model_functions(self):
        # self.profile.rebuild_customers()
        # self.profile.rebuild_churns()

        print len(self.profile.customers), 'customers'
        print len(self.profile.churns), 'churns'

        print self.profile.average_monthly_revenue(), 'monthly revenue'
        print self.profile.average_monthly_revenue_per_user(), 'average customer revenue'
        print self.profile.customer_count_past_days(), 'customers 30 days'
        print self.profile.churn_count_past_days(), 'churns 30 days'
        print self.profile.churn(), '% churn of 30 day'
        print self.profile.customer_lifetime_value(), 'CLV in cents'
        print self.profile.periods()