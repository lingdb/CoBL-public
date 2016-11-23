# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0124_remove_lexemes_without_meaning'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lexeme',
            name='meaning',
            field=models.ForeignKey(to='lexicon.Meaning'),
        ),
    ]
