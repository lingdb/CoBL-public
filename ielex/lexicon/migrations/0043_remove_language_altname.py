# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0042_languages_unjson'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='language',
            name='altname',
        ),
    ]
