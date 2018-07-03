# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0022_author'),
    ]

    operations = [
        migrations.AddField(
            model_name='languagebranches',
            name='shortName',
            field=models.CharField(max_length=5, blank=True),
        ),
    ]
