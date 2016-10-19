# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0109_nexusexport__exportbeauti'),
    ]

    operations = [
        migrations.AddField(
            model_name='language',
            name='latitude',
            field=models.DecimalField(
                null=True, max_digits=19, decimal_places=10),
        ),
        migrations.AddField(
            model_name='language',
            name='longitude',
            field=models.DecimalField(
                null=True, max_digits=19, decimal_places=10),
        ),
    ]
