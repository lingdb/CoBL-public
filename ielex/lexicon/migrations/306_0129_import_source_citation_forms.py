# -*- coding: utf-8 -*-
# Inspired by:
# https://github.com/lingdb/CoBL/issues/223#issuecomment-256815113
from __future__ import unicode_literals, print_function
from django.db import migrations
from ielex.source_scripts.csv_source_import import import_csv_citations


def forwards_func(apps, schema_editor):
    import_csv_citations('lexicon_source.csv')


def reverse_func(apps, schema_editor):
    print('Reverse of 306_0128_import_source_citation_forms does nothing.')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '306_0128_auto_20161104_0119')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
