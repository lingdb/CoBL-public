# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations


def forwards_func(apps, schema_editor):
    '''
    All CognateJudgementCitation entries that
    are on the `Current` and `Jena200` lists
    need to have a reliability of `High`.
    '''
    # Models to work with:
    CognateJudgementCitation = apps.get_model(
        'lexicon', 'CognateJudgementCitation')
    MeaningList = apps.get_model('lexicon', 'MeaningList')
    LanguageList = apps.get_model('lexicon', 'LanguageList')
    Lexeme = apps.get_model('lexicon', 'Lexeme')
    # Interesting data:
    try:
        lList = LanguageList.objects.get(name='Current')
        mList = MeaningList.objects.get(name='Jena200')
        languageIds = lList.languages.values_list('id', flat=True)
        meaningIds = mList.meanings.values_list('id', flat=True)
        lexemeIds = Lexeme.objects.filter(
            language_id__in=languageIds,
            meaning_id__in=meaningIds).values_list('id', flat=True)
        # Entries to modify:
        cjcs = CognateJudgementCitation.objects.filter(
            cognate_judgement__lexeme_id__in=lexemeIds)
        # Setting reliability to high:
        cjcs.update(reliability='A')
    except LanguageList.DoesNotExist:
        pass
    except MeaningList.DoesNotExist:
        pass


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0091_bhojpuri')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
