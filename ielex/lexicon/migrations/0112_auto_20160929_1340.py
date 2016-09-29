# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0111_fill_language_latlon'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='meaning',
            options={'ordering': ['elicitation', 'gloss']},
        ),
        migrations.AddField(
            model_name='meaning',
            name='elicitation',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='meaning',
            name='tooltip',
            field=models.TextField(blank=True),
        ),
    ]
