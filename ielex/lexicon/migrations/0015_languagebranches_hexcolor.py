# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0014_meaningLists'),
    ]

    operations = [
        migrations.AddField(
            model_name='languagebranches',
            name='hexColor',
            field=models.CharField(max_length=6, blank=True),
        ),
    ]
