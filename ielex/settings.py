# Django settings for ielex project.
import sys
import os.path
# import logging

# DEBUG = True
# TEMPLATE_DEBUG = DEBUG

ROOTDIR = os.path.abspath(os.path.dirname(__file__))
VERSION = "0.9"

# set this in local_settings.py
# ADMINS = ( ('Your Name', 'your_email@domain.com'),)
# MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Amsterdam'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(ROOTDIR, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".

# STATIC_ROOT is defined in local_settings.py
STATIC_URL = '/static/'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'ielex.context_processors.configuration',
    'ielex.context_processors.navigation',
    )

MIDDLEWARE_CLASSES = (
    'django.middleware.transaction.TransactionMiddleware',
    'django.middleware.common.CommonMiddleware', # provides APPEND_SLASH
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'ielex.middleware.NoBlankLinesMiddleware', # does this cost much speed?
    'reversion.middleware.RevisionMiddleware',
)

ROOT_URLCONF = 'ielex.urls'

TEMPLATE_DIRS = (
     os.path.join(ROOTDIR, 'templates'), 
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'reversion',
    'south',
    'ielex.lexicon',
    'ielex.extensional_semantics',
    'ielex.website',
)

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

# -- local settings file, overrides settings.py ------------------
local_settings_path = os.path.join(ROOTDIR, "local_settings.py")
if not os.path.exists(local_settings_path):
    ## create default local settings
    import random
    settings_template = file(os.path.join(ROOTDIR,
        "local_settings.py.dist")).read()
    key_chars = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
    secret_key = "".join([random.choice(key_chars) for i in range(50)])
    print>>file(local_settings_path, "w"), settings_template.replace("<++>",
            secret_key)
from local_settings import *
# ----------------------------------------------------------------

if "test" in sys.argv:
    # overwrite DATABASES with sqlite in-memory database for tests
    DEBUG = TEMPLATE_DEBUG = False
    SOUTH_TESTS_MIGRATE = False
    SKIP_SOUTH_TESTS = True
    semantic_domains = True
    DATABASES = {
        'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
                'USER': '',
                'PASSWORD': '',
                'HOST': '',
                'PORT': '',
        },
    }
    LIMIT_TO = 4 # limit lexicon searches to four items


if DEBUG:
    try:
        import debug_toolbar
        MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
        INTERNAL_IPS = ('127.0.0.1',)
        INSTALLED_APPS += ('debug_toolbar',)
        # DEBUG_TOOLBAR_CONFIG = {'INTERCEPT_REDIRECTS':False}
    except ImportError:
        pass

