# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '306_0116_auto_20160930_1750'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
