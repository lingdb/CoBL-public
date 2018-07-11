# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0052_language_backup_sndcomp_levels'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lexeme',
            name='denormalized_cognate_classes',
        ),
    ]
