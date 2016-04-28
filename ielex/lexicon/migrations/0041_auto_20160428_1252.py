# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0040_auto_20160421_1450'),
    ]

    operations = [
        migrations.AddField(
            model_name='language',
            name='author',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='foss_stat',
            field=models.BooleanField(default=0),
        ),
        migrations.AddField(
            model_name='language',
            name='glottocode',
            field=models.CharField(max_length=8, null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='level0',
            field=models.IntegerField(default=0, null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='level1',
            field=models.IntegerField(default=0, null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='level2',
            field=models.IntegerField(default=0, null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='level3',
            field=models.IntegerField(default=0, null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='low_stat',
            field=models.BooleanField(default=0),
        ),
        migrations.AddField(
            model_name='language',
            name='mean_timedepth_BP_years',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='representative',
            field=models.BooleanField(default=0),
        ),
        migrations.AddField(
            model_name='language',
            name='reviewer',
            field=models.CharField(max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='rfcWebPath1',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='language',
            name='rfcWebPath2',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='language',
            name='soundcompcode',
            field=models.CharField(max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='std_deviation_timedepth_BP_years',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='variety',
            field=models.CharField(max_length=64, null=True),
        ),
    ]
