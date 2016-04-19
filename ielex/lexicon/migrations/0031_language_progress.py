# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0030_auto_20160419_1254'),
    ]

    operations = [
        migrations.AddField(
            model_name='language',
            name='progress',
            field=models.IntegerField(
                default=0,
                choices=[(0, b'No data'),
                         (1, b'Highly problematic'),
                         (2, b'Limited revision, still unreliable'),
                         (3, b'Revision underway'),
                         (4, b'Revision complete'),
                         (5, b'Second review complete')]),
        ),
    ]
