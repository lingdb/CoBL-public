# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0003_dyen_name_data_migration'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dyenname',
            name='language',
        ),
        migrations.DeleteModel(
            name='DyenName',
        ),
    ]
