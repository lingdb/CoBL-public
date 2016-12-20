# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-20 13:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexicon', '0135_auto_20161217_1524'),
    ]

    operations = [
        migrations.AddField(
            model_name='nexusexport',
            name='ascertainment_marker',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='nexusexport',
            name='dialect',
            field=models.CharField(choices=[('BP', 'BayesPhylogenies'),
                                            ('NN', 'NeighborNet'),
                                            ('MB', 'MrBayes')],
                                   default='NN',
                                   max_length=128),
        ),
        migrations.AddField(
            model_name='nexusexport',
            name='excludeDubious',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='nexusexport',
            name='excludeIdeophonic',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='nexusexport',
            name='excludeLoanword',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='nexusexport',
            name='excludeMarkedLanguages',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='nexusexport',
            name='excludeMarkedMeanings',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='nexusexport',
            name='excludeNotSwadesh',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='nexusexport',
            name='excludePllDerivation',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='nexusexport',
            name='excludePllLoan',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='nexusexport',
            name='includePllLoan',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='nexusexport',
            name='label_cognate_sets',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='nexusexport',
            name='language_list_name',
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name='nexusexport',
            name='meaning_list_name',
            field=models.CharField(blank=True, max_length=128),
        ),
    ]
