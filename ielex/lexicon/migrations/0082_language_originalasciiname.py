# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ielex.lexicon.validators


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0081_language_entrytimeframe'),
    ]

    operations = [
        migrations.AddField(
            model_name='language',
            name='originalAsciiName',
            field=models.CharField(
                default='', max_length=128,
                validators=[ielex.lexicon.validators.suitable_for_url]),
            preserve_default=False,
        ),
    ]
