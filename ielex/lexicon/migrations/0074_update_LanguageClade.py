# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import ielex.lexicon.models as models
from ielex.languageCladeLogic import updateLanguageCladeRelations


def forwards_func(apps, schema_editor):
    updateLanguageCladeRelations()


def reverse_func(apps, schema_editor):
    print('Nothing to do for reverse_func of 0074_update_LanguageClade')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0073_remove_lexeme_number_cognate_coded')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
