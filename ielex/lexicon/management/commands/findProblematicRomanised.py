# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from django.core.management import BaseCommand
from ielex.lexicon.models import Lexeme, LanguageList, MeaningList


class Command(BaseCommand):

    help = "Lists problematic lexemes according to a set of problematic " \
           "characters for the romanised attribute."

    def handle(self, *args, **options):
        languageList = LanguageList.objects.get(name=LanguageList.DEFAULT)
        meaningList = MeaningList.objects.get(name=MeaningList.DEFAULT)
        lexemes = Lexeme.objects.filter(
            language__in=languageList.languages.all(),
            meaning__in=meaningList.meanings.all())
        problematic = {
            'с', 'ध', '’', 'भ', 'о', 'շ', 'а', 'ր', 'प', 'φ', 'й', 'ι',
            'տ', 'ш', 'و', 'ջ', 'լ', 'δ', 'е', 'υ', 'թ', 'т', 'τ', 'ե',
            'γ', 'ج', '√', 'ն', 'պ', 'ς', 'ε', 'յ', 'к', 'վ', 'ӕ', 'р',
            'آ', 'س', 'ب', '‘', 'ت', 'ք', 'र', 'ի', 'հ', 'ց', 'ف', 'η',
            'ή', 'մ', 'д', 'կ', 'ւ', 'ر', 'ը', 'μ', 'ὐ', 'κ', 'ό', 'د',
            'ا', '—', 'խ', 'զ', 'м', 'ν', 'х', 'ղ', 'ھ', 'پ', 'ύ', 'н',
            'ս', 'λ', 'ա', 'ո', 'ο', 'ώ', 'ρ', 'ल', 'σ', 'я', 'п', 'ռ',
            'и'}
        for lexeme in lexemes.all():
            if len(problematic & (set(lexeme.romanised))):
                print('"%s","%s","%s","%s"' % (lexeme.id,
                                               lexeme.meaning,
                                               lexeme.romanised,
                                               lexeme.nativeScript))
