# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from django.db import migrations


def forwards_func(apps, schema_editor):
    Lexeme = apps.get_model('lexicon', 'Lexeme')
    fields = ['phoneMic',
              'transliteration',
              'not_swadesh_term',
              'rfcWebLookup1',
              'rfcWebLookup2',
              'dubious']
    print('Copying JSON data to dedicated columns.')
    for l in Lexeme.objects.all():
        for f in fields:
            if f in l.data:
                setattr(l, f, l.data[f])
        l.save()


def reverse_func(apps, schema_editor):
    print('Nothing to do for reverse_func of 0069_lexeme_unjson')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0068_auto_20160510_1835')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
