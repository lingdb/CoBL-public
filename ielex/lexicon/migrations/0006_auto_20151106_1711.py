# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ielex.lexicon.validators


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0005_rename_Language_data_to_altname'),
    ]

    operations = [
        migrations.AlterField(
            model_name='meaning',
            name='gloss',
            field=models.CharField(unique=True, max_length=64, validators=[ielex.lexicon.validators.suitable_for_url]),
        ),
    ]
