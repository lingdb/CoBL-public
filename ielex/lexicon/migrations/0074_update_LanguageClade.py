# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from django.db import migrations
from ielex.languageCladeLogic import mkUpdateLanguageCladeRelations


def forwards_func(apps, schema_editor):
    updateLanguageCladeRelations = mkUpdateLanguageCladeRelations(
        apps.get_model('lexicon', "Language"),
        apps.get_model('lexicon', "Language"),
        apps.get_model('lexicon', "Language"))
    updateLanguageCladeRelations()


def reverse_func(apps, schema_editor):
    print('Nothing to do for reverse_func of 0074_update_LanguageClade')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0073_remove_lexeme_number_cognate_coded')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
