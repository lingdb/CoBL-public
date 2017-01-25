# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from collections import defaultdict

from django.core.management import BaseCommand
from ielex.lexicon.models import Lexeme, LanguageList, MeaningList


class Command(BaseCommand):

    help = "Computes statistics for https://github.com/lingdb/CoBL/issues/380"

    def handle(self, *args, **options):
        languageList = LanguageList.objects.get(name=LanguageList.DEFAULT)
        meaningList = MeaningList.objects.get(name=MeaningList.DEFAULT)
        lexemes = Lexeme.objects.filter(
            language__in=languageList.languages.all(),
            meaning__in=meaningList.meanings.all())
        groups = {
            'halflings': [b'\\u02be', b'\\u02bf'],
            'punctuation': [b'&', b'[', b']', b':', b'+', b'\\xac', b'=', b'`',
                            b'\\u2011', b'\\u2018', b'\\u02d1', b'.',
                            b'\\u02c8', b'\\u02dc', b'~'],
            'segmental': [b'\\u03c9', b'\\u03ce', b'\\u021b', b'\\u0219',
                          b'\\xd8', b'\\u01ab', b'\\u02b7', b'\\u1d5b',
                          b'\\u2071', b'\\u1d35', b'\\u02b8', b'\\u1d64',
                          b'\\u02b0', b'\\u2082', b'\\u02e4', b'\\u0261',
                          b'\\u1e55']
        }
        for gName, gElements in  groups.items():
            groups[gName] = set([
                e.decode('unicode_escape') for e in gElements])
        buckets = defaultdict(list)
        for lexeme in lexemes.all():
            rSet = set(lexeme.romanised)
            for gName, gSet in groups.items():
                if gSet & rSet:
                    buckets[gName].append(lexeme)

        for bName, lexemes in buckets.items():
            print('Check for %s:' % bName)
            for lexeme in lexemes:
                print('%s, %s, %s' % (lexeme.id, lexeme.meaning, lexeme.romanised))
