# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0117_source_active'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='source',
            name='author',
        ),
        migrations.RemoveField(
            model_name='source',
            name='editor',
        ),
        migrations.RemoveField(
            model_name='source',
            name='journal',
        ),
        migrations.RemoveField(
            model_name='source',
            name='publisher',
        ),
        migrations.RemoveField(
            model_name='source',
            name='series',
        ),
        migrations.AlterField(
            model_name='source',
            name='type',
            field=models.CharField(max_length=32, blank=True),
        ),
        migrations.DeleteModel(
            name='Journal',
        ),
        migrations.DeleteModel(
            name='Publisher',
        ),
        migrations.DeleteModel(
            name='Series',
        ),
    ]
