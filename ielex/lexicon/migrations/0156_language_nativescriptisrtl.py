# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2018-03-03 20:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0155_auto_20171216_1416'),
    ]

    operations = [
        migrations.AddField(
            model_name='language',
            name='nativeScriptIsRtl',
            field=models.BooleanField(default=0),
        ),
    ]
