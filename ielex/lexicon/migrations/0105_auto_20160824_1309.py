# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0104_convert_language_distributions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='language',
            name='mean_timedepth_BP_years',
        ),
        migrations.RemoveField(
            model_name='language',
            name='std_deviation_timedepth_BP_years',
        ),
    ]
