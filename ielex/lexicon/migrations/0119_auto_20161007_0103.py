# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0118_auto_20161007_0102'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='author',
            field=models.CharField(max_length=128, blank=True),
        ),
        migrations.AddField(
            model_name='source',
            name='editor',
            field=models.TextField(max_length=128, blank=True),
        ),
        migrations.AddField(
            model_name='source',
            name='journal',
            field=models.CharField(max_length=128, blank=True),
        ),
        migrations.AddField(
            model_name='source',
            name='publisher',
            field=models.CharField(max_length=128, blank=True),
        ),
        migrations.AddField(
            model_name='source',
            name='series',
            field=models.CharField(max_length=128, blank=True),
        ),
    ]
