# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0036_auto_20160420_1457'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clade',
            name='family_ix',
            field=models.IntegerField(default=0, null=True),
        ),
    ]
