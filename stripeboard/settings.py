# Django settings for stripeboard project.
import os
import sys

PATH = os.path.dirname(__file__)

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Bryan Helmig', 'bryan@zapier.com'),
)

MANAGERS = ADMINS

### HEROKU SETTINGS

import dj_database_url
DATABASES = {
    'default': dj_database_url.config(default='postgres://localhost')
}

if os.environ.get('REDISTOGO_URL', None):
    import urlparse

    redis_url = urlparse.urlparse(os.environ.get('REDISTOGO_URL', 'redis://localhost'))

    CACHES = {
        'default': {
            'BACKEND': 'redis_cache.RedisCache',
            'LOCATION': '{0}:{1}'.format(redis_url.hostname, redis_url.port),
            'OPTIONS': {
                'DB': 0,
                'PASSWORD': redis_url.password,
                'PARSER_CLASS': 'redis.connection.HiredisParser'
            }
        }
    }

    BROKER_URL = 'redis://{password}@{host}:{port}/{db}'.format(
        host=redis_url.hostname,
        port=redis_url.port,
        password=redis_url.password,
        db=0
    )


TIME_ZONE = 'America/Chicago'
LANGUAGE_CODE = 'en-us'
SITE_ID = 1

USE_I18N = True
USE_L10N = True

USE_TZ = True

MEDIA_ROOT = os.path.join(PATH, 'media')
MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(PATH, 'static')
STATIC_URL = '/static/'


STATICFILES_DIRS = (
    os.path.join(PATH, 'assets'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

SECRET_KEY = None

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'stripeboard.urls'

WSGI_APPLICATION = 'stripeboard.wsgi.application'

TEMPLATE_DIRS = (
    os.path.join(PATH, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',

    'djcelery',
    'crispy_forms',

    'stripeboard.board',
)

LOGIN_URL = '/'
AUTH_PROFILE_MODULE = 'board.Profile'

CELERY_IGNORE_RESULT = True

STRIPE_CLIENT_ID = os.environ.get('STRIPE_CLIENT_ID', None) # the application's id "ca_*"
STRIPE_CLIENT_SECRET = os.environ.get('STRIPE_CLIENT_SECRET', None) # the account api key "*"


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

try:
    from stripeboard.settings_local import *
except ImportError:
    pass

import djcelery
djcelery.setup_loader()
