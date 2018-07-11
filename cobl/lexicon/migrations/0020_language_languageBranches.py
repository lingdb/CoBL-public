# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from django.db import migrations

import cobl.lexicon.models as models


def forwards_func(apps, schema_editor):
    Language = apps.get_model('lexicon', 'Language')
    for l in Language.objects.all():
        print('Updating language: ', l)
        models.Language.updateClades(l)


def reverse_func(apps, schema_editor):
    print('Nothing to do for 0020_language_languageBranches')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0019_language_languagebranch')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
