# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from django.core.management import BaseCommand
from cobl.lexicon.models import Lexeme, LanguageList, MeaningList


class Command(BaseCommand):

    help = "Produces a list of distinct chars " \
           "in romanised fields in the database."

    def handle(self, *args, **options):
        languageList = LanguageList.objects.get(name=LanguageList.DEFAULT)
        meaningList = MeaningList.objects.get(name=MeaningList.DEFAULT)
        lexemes = Lexeme.objects.filter(
            language__in=languageList.languages.all(),
            meaning__in=meaningList.meanings.all())
        chars = set()
        for romanised in lexemes.values_list('romanised', flat=True):
            chars |= set(romanised)
        print('chars:', ' '.join(sorted(chars)))
