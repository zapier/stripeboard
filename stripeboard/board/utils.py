import requests
from datetime import datetime, timedelta
import time
import json


def epoch_utc(dt=None):
    if dt is None:
        dt = datetime.now()
    return long(time.mktime(dt.utctimetuple()))


def get_all(api_key, url, params):
    items = []

    count = 100
    params.update({'count': count})

    kontinue = True
    while kontinue:
        params.update({'offset': len(items)})

        r = requests.get(
            url=url,
            headers={'Content-Type': 'application/json'},
            params=params,
            auth=(api_key, '')
        )
        r.raise_for_status()
        items += r.json['data']

        # print url, len(items), 'of', r.json['count']

        if len(r.json['data']) < count:
            kontinue = False

    return items

def retrieve_paying_customers(api_key, params={}):
    '''
    Rudimentary collection of paying customers.
    '''
    params = (params or {}).copy()
    params.update({
        # 'created[lt]': epoch_utc(datetime.now() - timedelta(days=60)),
        'subscription': True
    })

    customers = get_all(api_key, 'https://api.stripe.com/v1/customers', params)
    # do not include anyone on a trial now
    customers = [c for c in customers if c['subscription'].get('trial_end', 0) < epoch_utc()]
    # only folks paying
    customers = [c for c in customers if c['subscription']['plan']['amount'] != 0]

    return customers

def retrieve_subscription_end_events(api_key, params={}):
    '''
    Pulls out all paid-to-free conversions, or, churns.

    This assumes you push users to free plans.
    '''
    days = 35
    params = (params or {}).copy()


    # PAID to FREE churns (switching a plan to free)
    params.update({
        'created[gt]': epoch_utc(datetime.now() - timedelta(days=days)),
        'type': 'customer.subscription.updated' # if no "free" plan, try customer.subscription.deleted but filter out trials
    })

    paid_to_free = get_all(api_key, 'https://api.stripe.com/v1/events', params)

    def is_paid_to_free(e):
        is_currently_free = e['data']['object'].get('plan', {}).get('amount', 1) == 0
        was_previously_paying = e['data'].get('previous_attributes', {}).get('plan', {}).get('amount', 0) != 0
        return is_currently_free and was_previously_paying

    # filter out normal free plan assigments
    paid_to_free = [e for e in paid_to_free if is_paid_to_free(e)]


    # DELETED ACCOUNT CHURNS (straight up deleting a paid plan)
    params.update({
        'created[gt]': epoch_utc(datetime.now() - timedelta(days=days)),
        'type': 'customer.subscription.deleted' # if no "free" plan, try customer.subscription.deleted but filter out trials
    })

    deleted_subs = get_all(api_key, 'https://api.stripe.com/v1/events', params)

    def is_true_deletion(e):
        was_trialing = bool(e['data']['object'].get('trial_start', False))
        paid_plan_deleted = e['data']['object'].get('plan', {}).get('amount', 0) != 0
        return not was_trialing and paid_plan_deleted

    # filter out trial deletions
    deleted_subs = [e for e in deleted_subs if is_true_deletion(e)]


    return paid_to_free + deleted_subs
