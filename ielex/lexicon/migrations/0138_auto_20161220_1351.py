# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-20 13:51
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0137_normalize_nexus_exports'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='nexusexport',
            name='exportSettings',
        ),
    ]
