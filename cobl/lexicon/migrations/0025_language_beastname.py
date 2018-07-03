# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0024_auto_20160407_1428'),
    ]

    operations = [
        migrations.AddField(
            model_name='language',
            name='beastName',
            field=models.CharField(max_length=128, blank=True),
        ),
    ]
