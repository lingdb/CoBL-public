# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0101_language_notinexport'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clade',
            name='logNormalStDev',
            field=models.DecimalField(null=True, max_digits=19, decimal_places=10),
        ),
    ]
