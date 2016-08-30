# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from django.db import migrations

# setColors :: [{name :: String, color :: String}]
setColors = [{'name': 'ALL Indic',        'color': 'E11D21'},
             {'name': 'ALL Iranic',       'color': 'EEA2BE'},
             {'name': 'ALL Anatolian',    'color': '654321'},
             {'name': 'Tocharian',        'color': 'C9BA9D'},
             {'name': 'ALL Balto-Slavic', 'color': 'FFFF00'},
             {'name': 'Baltic',           'color': 'FF6701'},
             {'name': 'Armenian',         'color': '7E0B80'},
             {'name': 'Albanian',         'color': '999999'},
             {'name': 'ALL Greek',        'color': '97E7FF'},
             {'name': 'ALL Germanic',     'color': '002146'},
             {'name': 'ALL Romance',      'color': '66FF00'},
             {'name': 'ALL Celtic',       'color': '006301'}]


def forwards_func(apps, schema_editor):
    LanguageBranches = apps.get_model("lexicon", "LanguageBranches")
    print('Coloring LanguageBranches…')
    for set in setColors:
        try:
            branch = LanguageBranches.objects.get(
                level1_branch_name=set['name'])
            branch.hexColor = set['color']
            branch.save()
        except:
            print('Could not color Branch: ', set['name'])


def reverse_func(apps, schema_editor):
    LanguageBranches = apps.get_model("lexicon", "LanguageBranches")
    print('Discoloring LanguageBranches…')
    for set in setColors:
        try:
            branch = LanguageBranches.objects.get(
                level1_branch_name=set['name'])
            branch.hexColor = ''
            branch.save()
        except:
            print('Could not discolor Branch: ', set['name'])


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0016_languagebranches_armenian')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
