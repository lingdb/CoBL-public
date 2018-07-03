"""
WSGI config for CoBL project.
"""

import os
from urllib.parse import urlparse
from configparser import ConfigParser

from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler

from cobl import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cobl.settings")


def main(*args, **kw):
    cfg = ConfigParser(converters={'url': urlparse})
    cfg.read_dict(dict(main=kw))
    if cfg.has_option('main', 'sqlalchemy.url'):
        sqlaurl = cfg.geturl('main', 'sqlalchemy.url')
        if sqlaurl.scheme.startswith('postgresql'):
            settings.DATABASES['default'] = {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': sqlaurl.path[1:],
                'USER': sqlaurl.username,
                'PASSWORD': sqlaurl.password or '',
                'HOST': sqlaurl.hostname or '',
                'PORT': str(sqlaurl.port) if sqlaurl.port else '',
            }

    settings.DEBUG = False
    if cfg.has_option('main', 'debug'):
        settings.DEBUG = cfg.getboolean('main', 'debug')

    if cfg.has_option('main', 'secret_key'):
        settings.SECRET_KEY = cfg.get('main', 'secret_key')

    return StaticFilesHandler(get_wsgi_application())
