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
        problematic = set("իल″յցप’яθջкхجոήبھفτա‘ύմرиدρռسधتὐթ′ᴵκλآاղμε"
                          "йсսքլ₂рυըӕوδ√տկеրχόιպնоыφνдώтվηշнरап—զभοեپς"
                          "σհւխшγм")
        for lexeme in lexemes.all():
            if len(problematic & (set(lexeme.romanised))):
                print('"%s","%s","%s","%s"' % (lexeme.id,
                                               lexeme.meaning,
                                               lexeme.romanised,
                                               lexeme.nativeScript))
