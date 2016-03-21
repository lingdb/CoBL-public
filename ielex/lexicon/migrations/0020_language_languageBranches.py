# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import ielex.lexicon.models as models


def forwards_func(apps, schema_editor):
    for l in models.Language.objects.all():
        print('Updating language: ', l)
        l.updateLanguageBranch()


def reverse_func(apps, schema_editor):
    print('Nothing to do for 0020_language_languageBranches')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0019_language_languagebranch')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
