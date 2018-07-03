# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0034_auto_20160419_1657'),
    ]

    operations = [
        migrations.CreateModel(
            name='Clade',
            fields=[
                ('id', models.AutoField(
                    verbose_name='ID',
                    serialize=False,
                    auto_created=True,
                    primary_key=True)),
                ('family_ix', models.IntegerField(blank=True)),
                ('level1_branch_ix', models.IntegerField(default=0)),
                ('level2_branch_ix', models.IntegerField(default=0)),
                ('level3_branch_ix', models.IntegerField(default=0)),
                ('level1_branch_name', models.TextField(
                    unique=True, blank=True)),
                ('hexColor', models.CharField(max_length=6, blank=True)),
                ('shortName', models.CharField(max_length=5, blank=True)),
                ('export', models.BooleanField(default=0)),
                ('exportDate', models.BooleanField(default=0)),
                ('taxonsetName', models.CharField(max_length=100, blank=True)),
                ('atMost', models.IntegerField(null=True)),
                ('atLeast', models.IntegerField(null=True)),
                ('distribution', models.CharField(
                    default=b'_',
                    max_length=1,
                    choices=[(b'U', b'Uniform'),
                             (b'N', b'Normal'),
                             (b'L', b'Log normal'),
                             (b'O', b'Offset log normal'),
                             (b'_', b'None')])),
                ('logNormalOffset', models.IntegerField(null=True)),
                ('logNormalMean', models.IntegerField(null=True)),
                ('logNormalStDev', models.IntegerField(null=True)),
                ('normalMean', models.IntegerField(null=True)),
                ('normalStDev', models.IntegerField(null=True)),
                ('uniformUpper', models.IntegerField(null=True)),
                ('uniformLower', models.IntegerField(null=True)),
                ('cladeLevel0', models.IntegerField(default=0)),
                ('cladeLevel1', models.IntegerField(default=0)),
                ('cladeLevel2', models.IntegerField(default=0)),
                ('cladeLevel3', models.IntegerField(default=0)),
            ],
        ),
    ]
