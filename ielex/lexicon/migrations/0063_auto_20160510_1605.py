# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.datetime_safe


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0062_auto_20160510_1346'),
    ]

    operations = [
        migrations.AddField(
            model_name='clade',
            name='lastEditedBy',
            field=models.CharField(default=b'unknown', max_length=32),
        ),
        migrations.AddField(
            model_name='clade',
            name='lastTouched',
            field=models.DateTimeField(
                default=django.utils.datetime_safe.datetime.now,
                auto_now=True),
            preserve_default=False,
        ),
    ]
