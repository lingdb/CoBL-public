# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0075_clean_LanguageClade'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='source',
            name='data',
        ),
    ]
