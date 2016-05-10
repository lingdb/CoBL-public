# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0067_remove_meaning_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='lexeme',
            name='dubious',
            field=models.BooleanField(default=0),
        ),
        migrations.AddField(
            model_name='lexeme',
            name='not_swadesh_term',
            field=models.BooleanField(default=0),
        ),
        migrations.AddField(
            model_name='lexeme',
            name='phoneMic',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='lexeme',
            name='rfcWebLookup1',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='lexeme',
            name='rfcWebLookup2',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='lexeme',
            name='transliteration',
            field=models.TextField(blank=True),
        ),
    ]
