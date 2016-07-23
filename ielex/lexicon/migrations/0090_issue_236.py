# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.db.models import Max

from datetime import datetime


def forwards_func(apps, schema_editor):
    '''
    Computes statistics for https://github.com/lingdb/CoBL/issues/236
    '''
    # Models to work with:
    LanguageList = apps.get_model('lexicon', 'LanguageList')
    MeaningList = apps.get_model('lexicon', 'MeaningList')
    Meaning = apps.get_model('lexicon', 'Meaning')
    Lexeme = apps.get_model('lexicon', 'Lexeme')
    CognateClass = apps.get_model('lexicon', 'CognateClass')
    CognateJudgement = apps.get_model('lexicon', 'CognateJudgement')
    LanguageClade = apps.get_model('lexicon', 'LanguageClade')
    Clade = apps.get_model('lexicon', 'Clade')
    # Data to work with:
    current = LanguageList.objects.get(name='Current')
    jena200 = MeaningList.objects.get(name='Jena200')
    languageIds = current.languages.values_list('id', flat=True)
    meaningIds = jena200.meanings.values_list('id', flat=True)
    lexemeIds = Lexeme.objects.filter(
        language_id__in=languageIds,
        meaning_id__in=meaningIds).values_list('id', flat=True)
    cognateClassIds = CognateJudgement.objects.filter(
        lexeme_id__in=lexemeIds).values_list(
        'cognate_class_id', flat=True)
    cognateClasses = CognateClass.objects.filter(
        id__in=cognateClassIds,
        root_form='').all()  # Only without root_form is wanted.

    def compute(lowerBranchBound):
        # The computation we want to perform twice
        for cognateClass in cognateClasses:
            lexemeIds = CognateJudgement.objects.filter(
                cognate_class_id=cognateClass.id).values_list(
                'lexeme_id', flat=True)
            # Need to investigate lexemes:
            cladeNamesSet = set()
            for lexeme in Lexeme.objects.filter(
                    id__in=lexemeIds,
                    meaning_id__in=meaningIds).all():
                # Need to investigate clades:
                clades = Clade.objects.filter(
                    id__in=LanguageClade.objects.filter(
                        language_id=lexeme.language_id).values_list(
                        'clade_id', flat=True)).all()
                cladeNamesSet.add(', '.join([c.cladeName for c in clades]))
            # Yield interesting clades:
            if len(cladeNamesSet) > lowerBranchBound:
                cognateClass.bNames = ', '.join('"%s"' % n for
                                                n in cladeNamesSet)
                yield(cognateClass)
        yield(None)  # EOG

    def report(cognateClasses):
        # Print given cognateClasses:
        for cognateClass in cognateClasses:
            if cognateClass is None:
                continue
            lexemeIds = CognateJudgement.objects.filter(
                cognate_class_id=cognateClass.id).values_list(
                'lexeme_id', flat=True)
            meaningIds = Lexeme.objects.filter(
                id__in=lexemeIds).values_list('meaning_id', flat=True)
            meaningNames = Meaning.objects.filter(
                id__in=meaningIds).values_list('gloss', flat=True)
            meaningNames = ', '.join(['"%s"' % m for m in meaningNames])
            print("Cognate set id: %s meanings: %s branches: %s" %
                  (cognateClass.id,
                   meaningNames,
                   cognateClass.bNames))

    print('Task 1')
    report(compute(2))
    print('Task 2')
    report(compute(1))
    print(1/0)  # Break migration.


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [('lexicon', '0089_fix_citation')]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
