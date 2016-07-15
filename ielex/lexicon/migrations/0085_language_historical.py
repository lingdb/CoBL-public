# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0084_auto_20160713_1522'),
    ]

    operations = [
        migrations.AddField(
            model_name='language',
            name='historical',
            field=models.BooleanField(default=0),
        ),
    ]
