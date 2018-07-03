# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0025_language_beastname'),
    ]

    operations = [
        migrations.AddField(
            model_name='language',
            name='earliestTimeDepthBound',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='latestTimeDepthBound',
            field=models.IntegerField(null=True),
        ),
    ]
