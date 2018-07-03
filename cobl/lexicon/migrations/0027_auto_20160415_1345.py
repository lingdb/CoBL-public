# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0026_auto_20160408_1313'),
    ]

    operations = [
        migrations.AddField(
            model_name='languagebranches',
            name='atLeast',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='languagebranches',
            name='atMost',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='languagebranches',
            name='distribution',
            field=models.CharField(
                default=b'O',
                max_length=1,
                choices=[(b'U', b'Uniform'),
                         (b'N', b'Normal'),
                         (b'L', b'Log normal'),
                         (b'O', b'Offset log normal')]),
        ),
        migrations.AddField(
            model_name='languagebranches',
            name='export',
            field=models.BooleanField(default=0),
        ),
        migrations.AddField(
            model_name='languagebranches',
            name='level2_branch_ix',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='languagebranches',
            name='level3_branch_ix',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='languagebranches',
            name='logNormalMean',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='languagebranches',
            name='logNormalOffset',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='languagebranches',
            name='logNormalStDev',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='languagebranches',
            name='normalMean',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='languagebranches',
            name='normalStDev',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='languagebranches',
            name='sndcompLevel0',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='languagebranches',
            name='sndcompLevel1',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='languagebranches',
            name='sndcompLevel2',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='languagebranches',
            name='sndcompLevel3',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='languagebranches',
            name='taxonsetName',
            field=models.CharField(max_length=100, blank=True),
        ),
        migrations.AddField(
            model_name='languagebranches',
            name='uniformLower',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='languagebranches',
            name='uniformUpper',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='languagebranches',
            name='level1_branch_ix',
            field=models.IntegerField(default=0),
        ),
    ]
