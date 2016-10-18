# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0111_source_journal'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='publisher',
            field=models.ManyToManyField(to='lexicon.Publisher', blank=True),
        ),
        migrations.AddField(
            model_name='source',
            name='series',
            field=models.ForeignKey(blank=True, to='lexicon.Series', null=True),
        ),
    ]
