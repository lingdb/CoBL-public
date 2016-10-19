# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from django.db import migrations


def forwards_func(apps, schema_editor):
    CognateClass = apps.get_model('lexicon', 'CognateClass')
    fields = ['gloss_in_root_lang',
              'loanword',
              'loan_source',
              'loan_notes']
    print('Copying JSON data to dedicated columns.')
    for c in CognateClass.objects.all():
        for f in fields:
            if f in c.data:
                setattr(c, f, c.data[f])
        c.save()


def reverse_func(apps, schema_editor):
    print('Nothing to do for reverse_func of 0056_cognateclass_unjson')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0055_auto_20160504_1304')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
