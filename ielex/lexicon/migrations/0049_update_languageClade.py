# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import ielex.lexicon.models as models

import json


def forwards_func(apps, schema_editor):
    print('Updating clades for all languages..')
    Language = apps.get_model('lexicon', 'Language')
    for l in Language.objects.all():
        models.Language.updateClades(l)


def reverse_func(apps, schema_editor):
    LanguageClade = apps.get_model('lexicon', 'LanguageClade')
    print('Deleting all LanguageClade entries..')
    LanguageClade.objects.delete()


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0048_auto_20160502_1338')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
