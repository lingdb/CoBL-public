# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0069_lexeme_unjson'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lexeme',
            name='data',
        ),
    ]
