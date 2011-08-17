# Django settings for ielex project.
import os.path

# DEBUG = True
# TEMPLATE_DEBUG = DEBUG

VERSION = "0.4"
ROOTDIR = os.path.abspath(os.path.dirname(__file__))

# set this in local_settings.py
# ADMINS = ( ('Your Name', 'your_email@domain.com'),)
# MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(ROOTDIR, 'db.sqlite3'),
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Not used with sqlite3.
        'PORT': '',                      # Not used with sqlite3.
    }
}

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
ADMIN_MEDIA_PREFIX = '/admin_media/'

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
    'django.contrib.admin',
    'reversion',
    'south',
    'ielex.lexicon',
    'ielex.extensional_semantics',
)

# admin urls
LOGIN_URL = '/accounts/login/'
LOGOUT_URL = '/accounts/logout/'
LOGIN_REDIRECT_URL = '/accounts/profile/'

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

if DEBUG:
    try:
        import debug_toolbar
        MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
        INTERNAL_IPS = ('127.0.0.1',)
        INSTALLED_APPS += ('debug_toolbar',)
    except ImportError:
        pass

