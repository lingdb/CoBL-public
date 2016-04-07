# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0023_languagebranches_shortname'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='email',
            field=models.TextField(unique=True, blank=True),
        ),
        migrations.AlterField(
            model_name='author',
            name='initials',
            field=models.TextField(unique=True, blank=True),
        ),
    ]
