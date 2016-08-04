# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0078_fix_language_ascii_name'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='meaninglistorder',
            options={'ordering': ['meaning__gloss']},
        ),
    ]
