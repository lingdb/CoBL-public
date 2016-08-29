# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0105_auto_20160824_1309'),
    ]

    operations = [
        migrations.AddField(
            model_name='nexusexport',
            name='_constraintsData',
            field=models.BinaryField(null=True),
        ),
    ]
