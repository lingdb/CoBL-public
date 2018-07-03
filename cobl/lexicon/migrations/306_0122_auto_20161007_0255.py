# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '306_0121_source_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='institution',
            field=models.CharField(max_length=128, blank=True),
        ),
    ]
