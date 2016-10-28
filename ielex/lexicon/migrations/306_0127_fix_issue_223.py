# -*- coding: utf-8 -*-
# Inspired by:
# https://github.com/lingdb/CoBL/issues/223#issuecomment-256815113
from __future__ import unicode_literals, print_function
from django.db import migrations

sources_changes = {'merge': {157:[272], 78: [39], 33:[71], 93:[94],
                             236:[298], 44:[45], 365:[366], 368:[370],
                             84:[400], 423:[424, 425, 461]},
                   'delete': [21],
                   'deprecate': [42, 43, 44, 57, 58, 61, 64, 87, 88, 89,
                                 106, 107, 108, 109, 110, 111, 112, 113,
                                 114, 115, 117, 118, 119, 120, 123, 139,
                                 233]
                   }

def forwards_func(apps, schema_editor):
    from ielex.handle_duplicate_sources import *
    handle_sources(sources_changes)


def reverse_func(apps, schema_editor):
    print('Reverse of 306_0127_fix_issue223 does nothing.')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '306_0126_auto_20161027_0315')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
