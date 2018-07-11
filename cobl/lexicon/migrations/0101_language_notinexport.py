# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0100_nexusexport'),
    ]

    operations = [
        migrations.AddField(
            model_name='language',
            name='notInExport',
            field=models.BooleanField(default=0),
        ),
    ]
