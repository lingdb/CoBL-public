# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '306_0122_auto_20161007_0255'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='source',
            options={},
        ),
        migrations.RemoveField(
            model_name='source',
            name='active',
        ),
        migrations.RemoveField(
            model_name='source',
            name='type',
        ),
        migrations.RemoveField(
            model_name='source',
            name='type_code',
        ),
        migrations.AddField(
            model_name='source',
            name='deprecated',
            field=models.BooleanField(default=False),
        ),
    ]
