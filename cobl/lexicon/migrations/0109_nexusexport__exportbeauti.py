# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0108_auto_20160829_1556'),
    ]

    operations = [
        migrations.AddField(
            model_name='nexusexport',
            name='_exportBEAUti',
            field=models.BinaryField(null=True),
        ),
    ]
