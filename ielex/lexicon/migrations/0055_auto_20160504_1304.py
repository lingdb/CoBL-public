# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0054_author_timestamped'),
    ]

    operations = [
        migrations.AddField(
            model_name='cognateclass',
            name='gloss_in_root_lang',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='cognateclass',
            name='loan_notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='cognateclass',
            name='loan_source',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='cognateclass',
            name='loanword',
            field=models.BooleanField(default=0),
        ),
    ]
