# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from django.db import migrations


def forwards_func(apps, schema_editor):
    '''
    Setting reliability judgements for
    each LexemeCitation of each Lexeme
    in the current LanguageList to high:
    See https://github.com/lingdb/CoBL/issues/229
    '''
    # Models to work with:
    Lexeme = apps.get_model('lexicon', 'Lexeme')
    LanguageList = apps.get_model('lexicon', 'LanguageList')
    LexemeCitation = apps.get_model('lexicon', 'LexemeCitation')
    try:
        # Gathering data to work with:
        lList = LanguageList.objects.get(name='Current')
        languageIds = lList.languages.values_list('id', flat=True)
        lexemeIds = Lexeme.objects.filter(
            language_id__in=languageIds).values_list('id', flat=True)
        citations = LexemeCitation.objects.filter(lexeme_id__in=lexemeIds)
        # Fixing citations:
        for citation in citations:
            if citation.reliability != 'A':
                citation.reliability = 'A'
                citation.save()
    except LanguageList.DoesNotExist:
        pass


def reverse_func(apps, schema_editor):
    print('Nothing to do for reverse_func '
          'of 0088_set_lexical_citation_rel_high')


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0087_mark_excluded_lexemes_notSwh')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
