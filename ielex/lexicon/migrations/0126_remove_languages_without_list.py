# -*- coding: utf-8 -*-
# Inspired by:
# https://github.com/lingdb/CoBL/issues/223#issuecomment-256815113
from __future__ import unicode_literals, print_function
from django.db import migrations


def forwards_func(apps, schema_editor):
    LanguageListOrder = apps.get_model("lexicon", "LanguageListOrder")
    Language = apps.get_model("lexicon", "Language")

    unwanted = LanguageListOrder.objects.values_list('language_id', flat=True)

    query = Language.objects.exclude(id__in=unwanted)
    print('\nRemoving %s languages.' % query.count())
    query.delete()


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0125_copy_rfcWebLookup_for_greek')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
