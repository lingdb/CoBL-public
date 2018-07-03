# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from collections import defaultdict

from django.core.management import BaseCommand

from cobl.lexicon.models import CognateJudgement, Lexeme


class Command(BaseCommand):

    help = "Compiles a list of cognate classes,"\
           "\nwhere each cognate class belongs to more than one meaning."

    def handle(self, *args, **options):
        lexemeMeaningMap = dict(Lexeme.objects.values_list('id', 'meaning_id'))
        cogLexTuples = CognateJudgement.objects.values_list(
            'cognate_class_id', 'lexeme_id')

        cogMeaningMap = defaultdict(set)
        for cogId, lexId in cogLexTuples:
            cogMeaningMap[cogId].add(lexemeMeaningMap[lexId])

        for cogId, mIdSet in cogMeaningMap.items():
            if len(mIdSet) > 1:
                print("Cognate class %s has multiple meanings: %s." %
                      (cogId, mIdSet))
