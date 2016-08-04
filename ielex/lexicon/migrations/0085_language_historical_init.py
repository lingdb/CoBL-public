# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


def forwards_func(apps, schema_editor):
    '''
    This migration fills the `originalAsciiName` fields of
    Language models with copies of the `ascii_name` fields.
    https://github.com/lingdb/CoBL/issues/218
    '''
    Language = apps.get_model('lexicon', 'Language')
    for language in Language.objects.all():
        if language.mean_timedepth_BP_years is not None:
            if language.mean_timedepth_BP_years > 0:
                language.historical = True
                language.save()


def reverse_func(apps, schema_editor):
    print('Nothing to do for reverse_func of 0085_language_historical_init')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0085_language_historical')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
