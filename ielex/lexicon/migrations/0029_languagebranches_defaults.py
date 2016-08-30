# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from django.db import migrations


def forwards_func(apps, schema_editor):
    LanguageBranches = apps.get_model('lexicon', 'LanguageBranches')
    for lb in LanguageBranches.objects.all():
        if lb.distribution == 'O':
            lb.distribution = '_'
            lb.save()


def reverse_func(apps, schema_editor):
    print('Nothing to do for 0029_languabebranches_defaults')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0029_auto_20160419_1122')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
