# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import ielex.lexicon.models as models


def forwards_func(apps, schema_editor):
    '''
    Quickly written code for #225.
    '''
    Lexeme = models.Lexeme
    print("\n1: + lex. excl - Not swh")
    for l in Lexeme.objects.filter(not_swadesh_term=False).all():
        if l.is_excluded_lexeme:
            print(l.id)
    print("2: + lex .loan - Not swh")
    for l in Lexeme.objects.filter(not_swadesh_term=False).all():
        if l.is_loan_lexeme:
            print(l.id)
    print("3: + lex. loan")
    for l in Lexeme.objects.all():
        if l.is_loan_lexeme:
            print(l.id)
    print("4: 2 >= cognate sets - Not swh")
    for l in Lexeme.objects.filter(not_swadesh_term=False).all():
        if l.cognatejudgement_set.count() >= 2:
            print(l.id)
    print("5: + cog. excl.")
    for l in Lexeme.objects.all():
        if l.is_excluded_cognate:
            print(l.id)
    print("6: + cog. loan")
    for l in Lexeme.objects.all():
        if l.is_loan_cognate:
            print(l.id)
    print(1/0)


def reverse_func(apps, schema_editor):
    print('Nothing to do for reverse_func of 0085_foo')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0084_auto_20160713_1522')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
