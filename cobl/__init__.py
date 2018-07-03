"""
WSGI config for CoBL project.
"""

import os
from urllib.parse import urlparse
from configparser import ConfigParser
import pathlib

from django.core.wsgi import get_wsgi_application
from django.contrib.staticfiles.handlers import StaticFilesHandler

from cobl import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cobl.settings")


def main(global_settings, **kw):
    cfg_path = pathlib.Path(global_settings['__file__'])

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

    if cfg_path.parent.joinpath('secret_key').exists():
        with cfg_path.parent.joinpath('secret_key').open() as fp:
            settings.SECRET_KEY = fp.read()

    return StaticFilesHandler(get_wsgi_application())
