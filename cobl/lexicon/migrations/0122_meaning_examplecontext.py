# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '306_0132_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='meaning',
            name='exampleContext',
            field=models.CharField(max_length=128, blank=True),
        ),
    ]
