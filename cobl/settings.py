# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VERSION = "1.0"
DEBUG = False
SECRET_KEY = 'secret'

# Application definition

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dal',
    'dal_select2',
    'django.contrib.admin',
    'reversion',
    'cobl.lexicon',
    'cobl.extensional_semantics',
    'cobl.website',
    'django_tables2',
    'wtforms.ext.django',
)
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',  # provides APPEND_SLASH
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'cobl.middleware.NoBlankLinesMiddleware',  # does this cost much speed?
    'reversion.middleware.RevisionMiddleware',
)
ROOT_URLCONF = 'cobl.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR + '/cobl/templates'],
        # 'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.request',
                # required by django_tables2 for sorting
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'cobl.context_processors.configuration',
                'cobl.context_processors.navigation',
            ],
            'loaders': [('django.template.loaders.cached.Loader',
                         ['django.template.loaders.filesystem.Loader',
                          'django.template.loaders.app_directories.Loader']
                         )],
            'debug': False,  # reset in local_settings.py
        },
    },
]
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'coblx',
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Not used with sqlite3.
        'PORT': '',                      # Not used with sqlite3.
        'ATOMIC_REQUESTS': True,         # Required by sqlite3 (only)
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Amsterdam'  # TODO: # For Windows users:
#                                 need to set to same as system time zone?
USE_I18N = False  # Turning this off forces Django optimizations
#                   to avoid loading the internationalization machinery.
# USE_L10N = True
# USE_TZ = True

SITE_ID = 1

# admin urls
LOGIN_URL = '/login/'
LOGOUT_URL = '/logout/'
LOGIN_REDIRECT_URL = '/user/'

# --- setup logger ------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(message)s',
    handlers=[logging.StreamHandler()])

# Maximum number of search results
LIMIT_TO = 500

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'static')

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)
STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

DATA_UPLOAD_MAX_NUMBER_FIELDS = None

# A list of strings representing the host/domain names that this Django site can serve
ALLOWED_HOSTS = ["*"]

# Meta tags for the front page (<meta name=... /> format)
# e.g. the Google site verification tag could go here
META_TAGS = ""

ADMINS = ()
MANAGERS = ADMINS

DATE_FORMAT = "d M Y"
DATETIME_FORMAT = "l, dS F Y  H:i:s O"
SHORT_DATE_FORMAT = "d-m-Y"
SHORT_DATETIME_FORMAT = "Y-m-d H:i:s"

# Project customization
project_long_name = u"CoBL"
project_short_name = u"CoBL"  # should be different from all other projects
project_description = u"""Welcome to the CoBL website."""
project_citation = u"""Reference for data exported from project"""
acknowledgements = u""  # may include html markup

# Which modules to use (True or False)
semantic_domains = False
structural_features = False  # NotImplemented


# Overwrite settings from env:
if os.getenv('DEBUG'):
    DEBUG = os.getenv('DEBUG') == 'True'
if os.getenv('SECRET_KEY'):
    SECRET_KEY = os.getenv('SECRET_KEY')
for k1, k2 in [('DB_HOST', 'HOST'),
               ('DB_PORT', 'PORT'),
               ('DB_NAME', 'NAME'),
               ('DB_USER', 'USER'),
               ('DB_PASSWORD', 'PASSWORD')]:
    if os.getenv(k1):
        DATABASES['default'][k2] = os.getenv(k1)

if DEBUG:
    try:
        import debug_toolbar
        MIDDLEWARE_CLASSES += \
            ('debug_toolbar.middleware.DebugToolbarMiddleware',)
        INTERNAL_IPS = ('127.0.0.1',)
        INSTALLED_APPS += ('debug_toolbar',)
        # DEBUG_TOOLBAR_CONFIG = {'INTERCEPT_REDIRECTS':False}
        # Disable cached Loader:
        loaders = TEMPLATES[0]['OPTIONS']['loaders']
        if loaders[0][0] == 'django.template.loaders.cached.Loader':
            TEMPLATES[0]['OPTIONS']['loaders'] = loaders[0][1]
            print('Disabled cached Loader.')
    except ImportError:
        pass
    TEMPLATES[0]["OPTIONS"]["debug"] = True
