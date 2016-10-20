# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0120_auto_20161019_1545'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='edition',
            field=models.CharField(default='', max_length=128, blank=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='source',
            name='number',
            field=models.CharField(default='', max_length=128, blank=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='source',
            name='shorthand',
            field=models.CharField(max_length=16, blank=True),
        ),
        migrations.AlterField(
            model_name='source',
            name='volume',
            field=models.CharField(max_length=128, blank=True),
        ),
        migrations.AlterField(
            model_name='source',
            name='year',
            field=models.CharField(max_length=16, null=True, blank=True),
        ),
    ]
