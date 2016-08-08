# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


def forwards_func(apps, schema_editor):
    '''
    OldPersian doesn't have lexemes for some meanings.
    This migration generates them.
    '''
    # Models to work with:
    Language = apps.get_model('lexicon', 'Language')
    MeaningList = apps.get_model('lexicon', 'MeaningList')
    Lexeme = apps.get_model('lexicon', 'Lexeme')
    # Data to work with:
    target = Language.objects.get(ascii_name='OldPersian')
    # Mapping meaning.id -> Lexeme
    mIdLexemeMap = {}
    for l in Lexeme.objects.filter(language=target).all():
        mIdLexemeMap[l.meaning_id] = l
    # Searching for missing lexemes:
    mList = MeaningList.objects.get(name='Jena200')
    for m in mList.meanings.all():
        if m.id not in mIdLexemeMap:
            Lexeme.objects.create(
                meaning=m,
                language=target)


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0092_set_cjc_reliabilities_high')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
