# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from django.db import migrations


idDistributionMap = {
    80: {'normalMean': 3450, 'normalStDev': 125},
    133: {'normalMean': 3350, 'normalStDev': 75},
    134: {'normalMean': 2350, 'normalStDev': 50},
    135: {'normalMean': 3500, 'normalStDev': 100},
    81: {'normalMean': 1375, 'normalStDev': 75},
    82: {'normalMean': 1350, 'normalStDev': 75},
    173: {'normalMean': 3350, 'normalStDev': 55},
    110: {'normalMean': 2400, 'normalStDev': 32},
    177: {'normalMean': 1900, 'normalStDev': 20},
    188: {'normalMean': 40, 'normalStDev': 10},
    129: {'normalMean': 1550, 'normalStDev': 25},
    105: {'logNormalOffset': 3000, 'logNormalMean': 700,
          'logNormalStDev': 0.8},
    228: {'normalMean': 2750, 'normalStDev': 100},
    227: {'normalMean': 2700, 'normalStDev': 200},
    162: {'normalMean': 2450, 'normalStDev': 75},
    128: {'normalMean': 3200, 'normalStDev': 300},
    174: {'normalMean': 1500, 'normalStDev': 125},
    136: {'normalMean': 1350, 'normalStDev': 150},
    237: {'normalMean': 2450, 'normalStDev': 75},
    131: {'normalMean': 2450, 'normalStDev': 75},
    178: {'normalMean': 1600, 'normalStDev': 150},
    179: {'normalMean': 2100, 'normalStDev': 150},
    108: {'normalMean': 500, 'normalStDev': 50},
    100: {'normalMean': 1000, 'normalStDev': 50},
    252: {'normalMean': 351, 'normalStDev': 1},
    251: {'normalMean': 405, 'normalStDev': 1},
    250: {'normalMean': 330, 'normalStDev': 1},
    245: {'normalMean': 795, 'normalStDev': 107},
    238: {'normalMean': 600, 'normalStDev': 50},
    176: {'normalMean': 320, 'normalStDev': 20},
    243: {'normalMean': 656, 'normalStDev': 31},
    107: {'normalMean': 1650, 'normalStDev': 25},
    109: {'normalMean': 775, 'normalStDev': 75},
    157: {'normalMean': 650, 'normalStDev': 75},
    160: {'normalMean': 9999, 'normalStDev': 999},
    126: {'normalMean': 1050, 'normalStDev': 50},
    99: {'normalMean': 1050, 'normalStDev': 50},
    112: {'normalMean': 2050, 'normalStDev': 75},
    207: {'normalMean': 130, 'normalStDev': 15},
    209: {'normalMean': 900, 'normalStDev': 150},
    203: {'normalMean': 700, 'normalStDev': 50},
    204: {'normalMean': 750, 'normalStDev': 75},
    130: {'normalMean': 2200, 'normalStDev': 75},
    132: {'normalMean': 2150, 'normalStDev': 75},
    140: {'normalMean': 2050, 'normalStDev': 125},
    148: {'normalMean': 1050, 'normalStDev': 75},
    172: {'normalMean': 450, 'normalStDev': 50},
    149: {'normalMean': 1050, 'normalStDev': 75},
    101: {'normalMean': 700, 'normalStDev': 100},
    231: {'normalMean': 700, 'normalStDev': 100},
    230: {'normalMean': 300, 'normalStDev': 50},
    150: {'normalMean': 1050, 'normalStDev': 75},
    127: {'normalMean': 1250, 'normalStDev': 50},
    147: {'normalMean': 200, 'normalStDev': 30}}


def forwards_func(apps, schema_editor):
    Language = apps.get_model("lexicon", "Language")
    languages = Language.objects.filter(
        id__in=set(idDistributionMap.keys())).all()
    for language in languages:
        for k, v in idDistributionMap[language.id].items():
            setattr(language, k, v)
        language.save()


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0144_clean_lexeme_romanised_2')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
