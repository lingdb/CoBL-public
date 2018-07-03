# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0102_auto_20160824_1214'),
    ]

    operations = [
        migrations.AddField(
            model_name='language',
            name='distribution',
            field=models.CharField(
                default=b'_',
                max_length=1,
                choices=[(b'U', b'Uniform'),
                         (b'N', b'Normal'),
                         (b'L', b'Log normal'),
                         (b'O', b'Offset log normal'),
                         (b'_', b'None')]),
        ),
        migrations.AddField(
            model_name='language',
            name='logNormalMean',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='logNormalOffset',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='logNormalStDev',
            field=models.DecimalField(
                null=True, max_digits=19, decimal_places=10),
        ),
        migrations.AddField(
            model_name='language',
            name='normalMean',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='normalStDev',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='uniformLower',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='uniformUpper',
            field=models.IntegerField(null=True),
        ),
    ]
