# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0120_auto_20161007_0248'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='type',
            field=models.CharField(max_length=4, blank=True),
        ),
    ]
