# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


def forwards_func(apps, schema_editor):
    '''
    The mean_timedepth_BP_years and std_deviation_timedepth_BP_years
    fields of the Language model will be removed in the next migration,
    because they're replaced in favor of the Language inheriting the
    AbstractDistribution model.
    To keep our data it is copied over as a normal distribution.
    '''
    # Models to work with:
    Language = apps.get_model('lexicon', 'Language')
    # Only historical languages have dates:
    for l in Language.objects.filter(historical=True).all():
        l.normalMean = l.mean_timedepth_BP_years
        l.normalStDev = l.std_deviation_timedepth_BP_years
        l.distribution = 'N'
        l.save()


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0103_auto_20160824_1300')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
