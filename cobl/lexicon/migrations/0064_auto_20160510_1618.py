# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.datetime_safe


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0063_auto_20160510_1605'),
    ]

    operations = [
        migrations.AddField(
            model_name='sndcomp',
            name='lastEditedBy',
            field=models.CharField(default=b'unknown', max_length=32),
        ),
        migrations.AddField(
            model_name='sndcomp',
            name='lastTouched',
            field=models.DateTimeField(
                default=django.utils.datetime_safe.datetime.now,
                auto_now=True),
            preserve_default=False,
        ),
    ]
