# A simple Stripe Dashboard

Stripe is awesome. Metrics are awesome. So let's do this!

## Try it.

Go check out a live, working version with OAuth at [http://board.zapier.com/](http://board.zapier.com/). Your data is in cache and sticks around for 24 hours, then you'll need to refresh it (we do not refresh it for you automatically).

![some made up numbers for example!](http://i.imgur.com/5CEvK.png)

### Heads up!

Trying to distill this information from Stripe's API is actually a bit tricky since we don't have a history of logged events (and downloading your entire Stripe DB via their API is not cool). So, we do our best to approximate it with a mixture of current customer snapshots, subscription update and deleted events. If you have a clever way to do this better, [we want to see it added](https://github.com/zapier/stripeboard/pulls)!


## Run it.

Well, first you need a Stripe application. You can read about that at [https://stripe.com/docs/apps/oauth](https://stripe.com/docs/apps/oauth).


### Heroku

Heroku makes this easy if you follow the docs found at [https://devcenter.heroku.com/articles/django](https://devcenter.heroku.com/articles/django). Below are some of the fancier things you'll need to do first to get it running...

You'll need the Redis To Go addon in Heroku:

```bash
# free version
heroku addons:add redistogo:nano
```

Here are some extra commands:

```bash
# your s3 config information
heroku config:add AWS_ACCESS_KEY_ID=xxx
heroku config:add AWS_SECRET_ACCESS_KEY=xxx
heroku config:add AWS_STORAGE_BUCKET_NAME=xxx
# a random secret key for django
heroku config:add SECRET_KEY=xxx
# the application's id "ca_*"
heroku config:add STRIPE_CLIENT_ID=xxx
# the account api key "*"
heroku config:add STRIPE_CLIENT_SECRET=xxx
```

And don't forget to scale out at least one worker:

```bash
# will cost you money...
heroku ps:scale celeryd=1
```

### Local

Be sure to `pip install requirements.txt` and have Redis running locally.

Create a `local_settings.py` file like so:

```python
DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'stripeboard.sqlite',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

BROKER_URL = 'redis://localhost:6379/0'

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': 'localhost:6379',
        'OPTIONS': {
            'DB': 0,
            'PARSER_CLASS': 'redis.connection.HiredisParser'
        },
    }
}

SECRET_KEY = 'FILLMEIN!'

MEDIA_URL = '/media/'
STATIC_URL = '/static/'

STRIPE_TEST_API_KEY = 'ONLYFORTESTS...'

STRIPE_CLIENT_ID = 'ASTRING' # the application's id "ca_*"
STRIPE_CLIENT_SECRET = 'ASTRING' # the account api key "*"
```

And run `foreman start` after doing all the standard `python manage.py syncdb` stuff.
