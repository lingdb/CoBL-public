# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from django.db import migrations


def forwards_func(apps, schema_editor):
    '''
    This migration fills the `originalAsciiName` fields of
    Language models with copies of the `ascii_name` fields.
    https://github.com/lingdb/CoBL/issues/218
    '''
    Language = apps.get_model('lexicon', 'Language')
    for language in Language.objects.all():
        language.originalAsciiName = language.ascii_name
        language.save()


def reverse_func(apps, schema_editor):
    print('Nothing to do for reverse_func of '
          '0082_language_fill_originalasciiname')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0082_language_originalasciiname')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
