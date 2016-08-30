# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from django.db import migrations

# data :: [{name :: String, meanings :: [{id :: Int, name :: String}]}]
data = [
        {'name': 'minitest',
         'meanings': [
            {'id': '82', 'name': 'I'},
            {'id': '137', 'name': 'see'},
            {'id': '183', 'name': 'two'},
            {'id': '30', 'name': 'dirty'},
            {'id': '51', 'name': 'fish'},
            {'id': '188', 'name': 'water'}]
         }]


def forwards_func(apps, schema_editor):
    MeaningList = apps.get_model("lexicon", "MeaningList")
    Meaning = apps.get_model("lexicon", "Meaning")
    MeaningListOrder = apps.get_model("lexicon", "MeaningListOrder")
    for ml in data:
        meaningList = MeaningList(name=ml['name'])
        meaningList.save()
        meaningList = MeaningList.objects.get(name=ml['name'])
        n = 1
        for m in ml['meanings']:
            try:
                meaning = Meaning.objects.get(id=m['id'])
                MeaningListOrder.objects.create(
                        meaning=meaning,
                        meaning_list=meaningList,
                        order=n)
                n += 1
            except:
                pass  # Meaning not found


def reverse_func(apps, schema_editor):
    MeaningList = apps.get_model("lexicon", "MeaningList")
    Meaning = apps.get_model("lexicon", "Meaning")
    MeaningListOrder = apps.get_model("lexicon", "MeaningListOrder")
    for ml in data:
        print('Removing meaning list: ', ml['name'])
        meaningList = MeaningList.objects.get(name=ml['name'])
        for m in ml['meanings']:
            meaning = Meaning.objects.get(id=m['id'])
            mlo = MeaningListOrder.objects.get(
                    meaning=meaning,
                    meaning_list=meaningList)
            mlo.delete()
        meaningList.delete()


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0106_nexusexport__constraintsdata')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
