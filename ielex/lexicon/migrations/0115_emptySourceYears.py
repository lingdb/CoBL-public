# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from django.db import migrations


def forwards_func(apps, schema_editor):
    Source = apps.get_model("lexicon", "Source")
    Source.objects.update(year='')


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0114_auto_20161018_1644')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
