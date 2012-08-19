from datetime import datetime, timedelta
import requests

from django.conf import settings
from django.core.cache import cache
from django.db import models

from stripeboard.board.utils import (retrieve_paying_customers,
                                     retrieve_subscription_end_events,
                                     epoch_utc)

TIMEOUT = 60 * 60 * 24


class Profile(models.Model):
    user = models.ForeignKey('auth.User', unique=True)

    livemode = models.NullBooleanField(null=True, blank=True)
    access_token = models.CharField(max_length=255, null=True, blank=True)
    refresh_token = models.CharField(max_length=255, null=True, blank=True)
    stripe_user_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_publishable_key = models.CharField(max_length=255, null=True, blank=True)


    def set(self, obj):
        self.livemode = obj['livemode'] == 'true'
        self.access_token = obj['access_token']
        self.refresh_token = obj['refresh_token']
        self.stripe_user_id = obj['stripe_user_id']
        self.stripe_publishable_key = obj['stripe_publishable_key']


    #########################
    ### STRIPE COLLECTION ###
    #########################

    CUSTOMERS_KEY = property(lambda self: 'stripe-paying-customers-{0}'.format(self.id))

    @property
    def customers(self):
        '''
        All paying customers (with subscriptions).
        '''
        return cache.get(self.CUSTOMERS_KEY, [])

    def rebuild_customers(self):
        if self.access_token:
            try:
                customers = retrieve_paying_customers(self.access_token)
            except requests.HTTPError:
                customers = self.refresh(next=self.rebuild_customers)
            cache.set(self.CUSTOMERS_KEY, customers, TIMEOUT)


    CHURNS_KEY = property(lambda self: 'stripe-churns-{0}'.format(self.id))

    @property
    def churns(self):
        '''
        All churns (subscription deleted).
        '''
        return cache.get(self.CHURNS_KEY, [])

    def rebuild_churns(self):
        if self.access_token:
            try:
                events = retrieve_subscription_end_events(self.access_token)
            except requests.HTTPError:
                events = self.refresh(next=self.rebuild_customers)
            cache.set(self.CHURNS_KEY, events, TIMEOUT)

    REBUILD_LOCK = property(lambda self: 'rebuild-lock-{0}'.format(self.id))

    def rebuild(self):
        from stripeboard.board.tasks import rebuild_cache

        # only one rebuild per hour
        lock = cache.get(self.REBUILD_LOCK, False)
        if lock:
            return False

        rebuild_cache.delay(self.user.id)
        cache.set(self.REBUILD_LOCK, True, 60*60)
        return True


    def refresh(self, next=None):
        '''
        When we 401, we'll try and grab a refresh token. If that fails, we
        clear out the oauth params we've saved.
        '''
        r = requests.post(
            url='https://connect.stripe.com/oauth/token',
            headers={'Accept': 'application/json',
                     'Authorization': 'Bearer {0}'.format(settings.STRIPE_CLIENT_SECRET)},
            data={'grant_type': 'refresh_token',
                  'client_id': settings.STRIPE_CLIENT_ID,
                  'scope': 'read_only',
                  'refresh_token': self.refresh_token})

        try:
            r.raise_for_status()
            self.set(r.json)
        except requests.HTTPError:
            # set all tokens to None
            from collections import defaultdict
            self.set(defaultdict(lambda: None))

        self.save()

        if callable(next):
            return next()
        return None


    ####################
    ### DATA SLICING ###
    ####################

    def customer_lifetime_value(self, days=31):
        churn = self.churn(days)

        if churn:
            return int(self.average_monthly_revenue_per_user() / (churn / 100))
        return 0

    def average_monthly_revenue(self):
        return sum(c['subscription']['plan']['amount'] for c in self.customers)

    def average_monthly_revenue_per_user(self):
        customers = self.customers
        if customers:
            return self.average_monthly_revenue() / len(customers)
        return 0

    def customer_count_past_days(self, days=31):
        '''
        A total count of customers in a period. A little trickier.

        Since churned customers will not be included in our most recent customer snapshot,
        we must partially add them back for a more accurate model. Partial because this
        is an average, so half.
        '''
        return len(self.customers) + (self.churn_count_past_days(days) / 2)

    def churn_count_past_days(self, days=31):
        '''
        Very simple, just the number of people who delete their subscription
        within a period (now-30d and now).
        '''
        start = epoch_utc(datetime.now() - timedelta(days=days))
        end = epoch_utc(datetime.now())
        return len([churn for churn in self.churns if start < churn['created'] < end])

    def churn(self, days=31):
        '''
        # churns in period / average # of customers in period
        '''
        denom = self.customer_count_past_days(days)
        if denom:
            return round((float(self.churn_count_past_days(days)) / denom) * 100, 2)
        return 0.0

    def periods(self, days=31):
        customers = list(self.customers)
        churns = list(self.churns)

        now = datetime.now().replace(hour=0, minute=0, second=0)
        periods = [{'timestamp': epoch_utc(now - timedelta(days=i))} for i in reversed(range(1, days+1))]

        for period in periods:
            period_customers = [cust for cust in customers if cust['created'] < period['timestamp']]
            period_churns = [churn for churn in churns if churn['created'] > period['timestamp']]
            period['customers'] = len(period_customers) + len(period_churns)
            period['monthly_revenue'] = sum(c['subscription']['plan']['amount'] for c in period_customers)
            period['monthly_revenue'] += sum(e['data']['object'].get('plan', {}).get('amount', 0) for e in period_churns)
            period['monthly_revenue'] = period['monthly_revenue'] / float(100)

        return periods

    @property
    def data(self):
        return {
            'monthly_revenue': self.average_monthly_revenue() / float(100),
            'average_monthly_revenue_per_user': self.average_monthly_revenue_per_user() / float(100),
            'paying_customers': len(self.customers),
            'churn_count': self.churn_count_past_days(),
            'churn': self.churn(),
            'customer_lifetime_value': self.customer_lifetime_value() / float(100),
            'periods': self.periods()}


from django.contrib.auth.models import User

def user_post_save(sender, instance, created, raw, **kwargs):
    if created:
        customuser = Profile.objects.create(user=instance)
models.signals.post_save.connect(user_post_save, sender=User)


### monkey patch ###
from django.db.models.signals import class_prepared

# from http://stackoverflow.com/questions/2610088
def longer_email_username(sender, *args, **kwargs):
    if sender.__name__ == 'User' and sender.__module__ == 'django.contrib.auth.models':
        sender._meta.get_field('username').max_length = 125
        sender._meta.get_field('email').max_length = 125
class_prepared.connect(longer_email_username)
