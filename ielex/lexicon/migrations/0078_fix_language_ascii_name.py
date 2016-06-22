# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import ielex.lexicon.models as models

import json


def forwards_func(apps, schema_editor):
    urlChars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                   "abcdefghijklmnopqrstuvwxyz"
                   "0123456789_.~-")
    Language = apps.get_model('lexicon', 'Language')
    for l in Language.objects.all():
        lChars = set(l.ascii_name)
        if(len(urlChars & lChars) > 0):
            l.ascii_name = ''.join([c for c in l.ascii_name if c in urlChars])
            l.save()


def reverse_func(apps, schema_editor):
    print('Nothing to do for reverse_func of 0078_fix_language_ascii_name')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0077_auto_20160602_1434')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
