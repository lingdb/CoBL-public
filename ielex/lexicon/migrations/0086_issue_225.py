# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import ielex.lexicon.models as models


def forwards_func(apps, schema_editor):
    '''
    Quickly written code for #225.
    '''
    MeaningList = models.MeaningList
    ml = MeaningList.objects.get(name=MeaningList.DEFAULT)
    Lexeme = models.Lexeme
    lexemes = Lexeme.objects.filter(
        meaning__in=ml.meanings.values_list('id', flat=True)).all()
    print("\n1: + lex. excl - Not swh")
    for l in lexemes:
        if not l.not_swadesh_term:
            if l.is_excluded_lexeme:
                print(l.id)
    print("2: + lex .loan - Not swh")
    for l in lexemes:
        if not l.not_swadesh_term:
            if l.is_loan_lexeme:
                print(l.id)
    print("3: + lex. loan")
    for l in lexemes:
        if l.is_loan_lexeme:
            print(l.id)
    print("4: 2 >= cognate sets - Not swh")
    for l in lexemes:
        if not l.not_swadesh_term:
            if l.cognatejudgement_set.count() >= 2:
                print(l.id)
    print("5: + cog. excl. - Not swh")
    for l in lexemes:
        if not l.not_swadesh_term:
            if l.is_excluded_cognate:
                print(l.id)
    print("6: + cog. loan - Not swh")
    for l in lexemes:
        if not l.not_swadesh_term:
            if l.is_loan_cognate:
                print(l.id)
    print(1/0)


def reverse_func(apps, schema_editor):
    print('Nothing to do for reverse_func of #225')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0085_language_historical_init')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
