# -*- coding: utf-8 -*-
# Inspired by:
# https://github.com/lingdb/CoBL/issues/223#issuecomment-256815113
from __future__ import unicode_literals, print_function
from django.db import migrations
from ielex.source_scripts.handle_duplicate_sources import handle_sources

sources_changes = {'merge': {},
                   'delete': [],
                   'deprecate': [35, 191, 139, 362]
                   }


def forwards_func(apps, schema_editor):
    handle_sources(sources_changes)


def reverse_func(apps, schema_editor):
    print('Reverse of 306_0131_deprecate_sources does nothing.')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '306_0130_auto_20161104_1721')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
