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


def configure(cfg_path):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cobl.settings")
    settings.DEBUG = False
    if not cfg_path:
        return
    cfg_path = pathlib.Path(cfg_path)
    cfg = ConfigParser(converters={'url': urlparse})
    cfg.read([str(cfg_path)])
    section = 'app:main' if cfg.has_section('app:main') else 'app:cobl'

    if cfg.has_option(section, 'sqlalchemy.url'):
        sqlaurl = cfg.geturl(section, 'sqlalchemy.url')
        if sqlaurl.scheme.startswith('postgresql'):
            settings.DATABASES['default'] = {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'NAME': sqlaurl.path[1:],
                'USER': sqlaurl.username,
                'PASSWORD': sqlaurl.password or '',
                'HOST': sqlaurl.hostname or '',
                'PORT': str(sqlaurl.port) if sqlaurl.port else '',
            }

    if cfg.has_option(section, 'debug'):
        settings.DEBUG = cfg.getboolean(section, 'debug')

    if cfg_path.parent.joinpath('secret_key').exists():
        with cfg_path.parent.joinpath('secret_key').open() as fp:
            settings.SECRET_KEY = fp.read()


def main(global_settings, **kw):
    configure(global_settings['__file__'])
    return StaticFilesHandler(get_wsgi_application())

