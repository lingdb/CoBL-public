# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0072_remove_language_beastname'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lexeme',
            name='number_cognate_coded',
        ),
    ]
