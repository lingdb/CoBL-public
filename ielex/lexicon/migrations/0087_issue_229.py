# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.db.models import Max


def forwards_func(apps, schema_editor):
    '''
    Printing all Lexemes from the `Current` LanguageList
    across all meanings, where:
    * at least one LexemeCitation has a reliability of 'X'
    * not_swadesh_term is False
    See https://github.com/lingdb/CoBL/issues/229
    '''
    # Models to work with:
    Lexeme = apps.get_model('lexicon', 'Lexeme')
    LanguageList = apps.get_model('lexicon', 'LanguageList')
    # Computing lexemes:
    lList = LanguageList.objects.get(name='Current')
    languageIds = lList.languages.values_list('id', flat=True)
    lexemes = Lexeme.objects.filter(language__in=languageIds).all()
    # Printing wanted lexemes:
    for lexeme in lexemes:
        reliabilities = set([lc.reliability for lc
                             in lexeme.lexemecitation_set.all()])
        if 'X' in reliabilities and not lexeme.not_swadesh_term:
            print(lexeme.id)
    print(1/0)  # Breaking migration


def reverse_func(apps, schema_editor):
    print('Nothing to do for reverse_func of 0087_issue_229')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0086_add_LateVedic_to_current')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
