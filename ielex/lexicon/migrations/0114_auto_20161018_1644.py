# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '306_0124_auto_20161018_1135'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='year',
            field=models.CharField(max_length=4, null=True, blank=True),
        ),
    ]
