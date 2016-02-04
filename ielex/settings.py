# -*- coding: utf-8 -*-
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VERSION = "1.0"

# SECURITY WARNING: keep the secret key used in production secret!
# SECURITY WARNING: don't run with debug turned on in production!

# SECRET_KEY = '##' ## Secret key is set in local_settings.py
# DEBUG = False ## Debug is set in local_settings.py
# ALLOWED_HOSTS = [] 

# Application definition

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'reversion',
    'ielex.lexicon',
    'ielex.extensional_semantics',
    'ielex.website',
    'django_tables2',
    'wtforms.ext.django',
)

MIDDLEWARE_CLASSES = (
    #'django.middleware.transaction.TransactionMiddleware',
    #    "TransactionMiddleware is deprecated in favor of ATOMIC_REQUESTS.",
    'django.middleware.common.CommonMiddleware', # provides APPEND_SLASH
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'ielex.middleware.NoBlankLinesMiddleware', # does this cost much speed?
    'reversion.middleware.RevisionMiddleware',

    #TODO: check whether these could be included.
    #'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    #'django.middleware.clickjacking.XFrameOptionsMiddleware',
    #'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'ielex.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['ielex/templates'],
        #'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'ielex.context_processors.configuration',
                'ielex.context_processors.navigation',
            ],
            'loaders' : [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                #'django.template.loaders.eggs.load_template_source',
            ],
            'debug':False, # reset in local_settings.py
        },
    },
]


#TODO: need this??
#WSGI_APPLICATION = '...'


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'ielex/db.sqlite3'),
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Not used with sqlite3.
        'PORT': '',                      # Not used with sqlite3.
        'ATOMIC_REQUESTS':True,          # Required by sqlite3 (only)
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Amsterdam' #TODO: # For Windows users: need to set to same as system time zone?
USE_I18N = False #Turning this off forces Django optimizations to avoid loading the internationalization machinery.
#USE_L10N = True
#USE_TZ = True

SITE_ID = 1

# admin urls
LOGIN_URL = '/login/'
LOGOUT_URL = '/logout/'
LOGIN_REDIRECT_URL = '/user/'

## -- setup logger ------------------------------------------------
# logging.basicConfig(level=logging.INFO,
#      format='%(asctime)s %(levelname)s %(message)s',
#      filename=os.path.join(os.path.dirname(ROOTDIR), 'django.log'),
#      filemode='a+')

# Default values (override in local_settings.py)
LIMIT_TO = 500

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/ielex/static/'
STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'static')

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)
#STATICFILES_DIRS = (
#    os.path.join(os.path.dirname(BASE_DIR), 'static'),
#)

#TODO: need following??
# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
#MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
#MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".


local_settings_path = os.path.join(BASE_DIR, "ielex/local_settings.py")
if not os.path.exists(local_settings_path):
    ## create default local settings
    import random
    settings_template = file(os.path.join(BASE_DIR,"ielex/local_settings.py")).read()
    key_chars = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
    secret_key = "".join([random.choice(key_chars) for i in xrange(50)])
    print>>file(local_settings_path, "w"), settings_template.replace("<++>",secret_key)
from local_settings import *


if DEBUG:
    try:
        import debug_toolbar
        MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
        INTERNAL_IPS = ('127.0.0.1',)
        INSTALLED_APPS += ('debug_toolbar',)
        # DEBUG_TOOLBAR_CONFIG = {'INTERCEPT_REDIRECTS':False}
    except ImportError:
        pass
    TEMPLATES[0]["OPTIONS"]["debug"] = True
