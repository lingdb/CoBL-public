# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0032_auto_20160419_1506'),
    ]

    operations = [
        migrations.AddField(
            model_name='languagebranches',
            name='exportDate',
            field=models.BooleanField(default=0),
        ),
    ]
