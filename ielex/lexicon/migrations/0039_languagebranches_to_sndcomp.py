# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


def forwards_func(apps, schema_editor):
    LanguageBranches = apps.get_model('lexicon', 'LanguageBranches')
    SndComp = apps.get_model('lexicon', 'SndComp')
    print('Creating SndComp from LanguageBranches.')
    for lb in LanguageBranches.objects.all():
        sndComp = SndComp(
            lgSetName=lb.level1_branch_name,
            lv0=lb.family_ix,
            lv1=lb.level1_branch_ix,
            lv2=lb.level2_branch_ix,
            lv3=lb.level3_branch_ix,
            cladeLevel0=lb.cladeLevel0,
            cladeLevel1=lb.cladeLevel1,
            cladeLevel2=lb.cladeLevel2,
            cladeLevel3=lb.cladeLevel3)
        sndComp.save()
    print('Created %s SndComp entries.' % SndComp.objects.count())


def reverse_func(apps, schema_editor):
    # Delete all clades:
    SndComp = apps.get_model('lexicon', 'SndComp')
    print('Deleting all SndComp models.')
    for s in SndComp.objects.all():
        s.delete()


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0038_sndcomp')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
