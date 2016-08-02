# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


def forwards_func(apps, schema_editor):
    LanguageBranches = apps.get_model("lexicon", "LanguageBranches")
    print('Adding Armenian LanguageBranch')
    branch = LanguageBranches(
        family_ix=9,
        level1_branch_ix=3,
        level1_branch_name='Armenian',
        hexColor='BF00FE')
    branch.save()


def reverse_func(apps, schema_editor):
    LanguageBranches = apps.get_model("lexicon", "LanguageBranches")
    branch = LanguageBranches.objects.get(
        family_ix=9, level1_branch_ix=3, level1_branch_name='Armenian')
    branch.delete()


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0015_languagebranches_hexcolor')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
