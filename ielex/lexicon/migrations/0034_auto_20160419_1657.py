# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0033_languagebranches_exportdate'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='author',
            options={'ordering': ['surname', 'firstNames']},
        ),
    ]
