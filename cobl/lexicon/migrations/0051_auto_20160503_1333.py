# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0050_auto_20160502_1520'),
    ]

    operations = [
        migrations.AddField(
            model_name='language',
            name='sndCompLevel0',
            field=models.IntegerField(default=0, null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='sndCompLevel1',
            field=models.IntegerField(default=0, null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='sndCompLevel2',
            field=models.IntegerField(default=0, null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='sndCompLevel3',
            field=models.IntegerField(default=0, null=True),
        ),
    ]
