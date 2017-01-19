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
        buckets = defaultdict(int)
        for lexeme in lexemes.all():
            for symbol in lexeme.romanised:
                buckets[symbol] += 1
        print('Symbol, Unicode, Occurences')
        for k, v in buckets.items():
            print("%s, %s, %s" % (k, k.encode('unicode_escape'), v))
