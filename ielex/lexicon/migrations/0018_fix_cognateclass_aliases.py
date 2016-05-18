# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import ielex.lexicon.models as models


def forwards_func(apps, schema_editor):
    CognateClass = apps.get_model('lexicon', 'CognateClass')
    for c in CognateClass.objects.filter(alias=''):
        print('Fixing alias for CognateClass: ', c.id)
        models.CognateClass.update_alias(c)


def reverse_func(apps, schema_editor):
    print('Nothing to do for 0018_fix_cognateclass_aliases')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0017_languagebranches_addColors')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
