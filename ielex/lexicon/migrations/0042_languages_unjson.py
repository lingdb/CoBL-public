# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


def forwards_func(apps, schema_editor):
    Language = apps.get_model('lexicon', 'Language')
    fieldMap = {
        'glottocode': 'glottocode',
        'variety': 'variety',
        'soundcompcode': 'soundcompcode',
        'level0': 'level0',
        'level1': 'level1',
        'level2': 'level2',
        'level3': 'level3',
        'mean_timedepth_BP_years': 'mean_timedepth_BP_years',
        'std_deviation_timedepth_BP_years': 'std_deviation_timedepth_BP_years',
        'foss_stat': 'foss_stat',
        'low_stat': 'low_stat',
        'representative': 'representative',
        'rfcWebPath1': 'rfcWebPath1',
        'rfcWebPath2': 'rfcWebPath2',
        'author': 'author',
        'reviewer': 'reviewer'}
    intFields = set(['level0',
                     'level1',
                     'level2',
                     'level3',
                     'mean_timedepth_BP_years',
                     'std_deviation_timedepth_BP_years'])
    print('Copying JSON data to dedicated columns.')
    for l in Language.objects.all():
        for k, v in fieldMap.iteritems():
            if k in l.altname:
                e = l.altname[k]
                if v in intFields:
                    try:
                        e = int(e)
                    except:
                        e = 0
                setattr(l, v, e)
        l.save()


def reverse_func(apps, schema_editor):
    print('Nothing to do for reverse_func of 0042_languages_unjson')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0041_auto_20160428_1252')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
