# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


def forwards_func(apps, schema_editor):
    LanguageBranches = apps.get_model('lexicon', 'LanguageBranches')
    Clade = apps.get_model('lexicon', 'Clade')
    fields = ['family_ix',
              'level1_branch_ix',
              'level2_branch_ix',
              'level3_branch_ix',
              'level1_branch_name',
              'hexColor',
              'shortName',
              'export',
              'exportDate',
              'taxonsetName',
              'atMost',
              'atLeast',
              'distribution',
              'logNormalOffset',
              'logNormalMean',
              'logNormalStDev',
              'normalMean',
              'normalStDev',
              'uniformUpper',
              'uniformLower',
              'cladeLevel0',
              'cladeLevel1',
              'cladeLevel2',
              'cladeLevel3']
    print('Creating clades from LanguageBranches.')
    for lb in LanguageBranches.objects.all():
        data = {f: getattr(lb, f) for f in fields}
        clade = Clade(**data)
        clade.save()
    print('Created %s clades.' % Clade.objects.count())


def reverse_func(apps, schema_editor):
    # Delete all clades:
    Clade = apps.get_model('lexicon', 'Clade')
    print('Deleting all clades.')
    for c in Clade.objects.all():
        c.delete()


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0034_clade')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
