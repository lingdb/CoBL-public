# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0048_language_sortrankinclade'),
    ]

    operations = [
        migrations.AddField(
            model_name='clade',
            name='level0Name',
            field=models.CharField(max_length=64, blank=True),
        ),
        migrations.AddField(
            model_name='clade',
            name='level1Name',
            field=models.CharField(max_length=64, blank=True),
        ),
        migrations.AddField(
            model_name='clade',
            name='level2Name',
            field=models.CharField(max_length=64, blank=True),
        ),
        migrations.AddField(
            model_name='clade',
            name='level3Name',
            field=models.CharField(max_length=64, blank=True),
        ),
    ]
