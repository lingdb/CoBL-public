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
            'Check_halflings': [b'\\u02be', b'\\u02bf'],
            'Check_punctuation': [
                b'&', b'[', b']', b':', b'+', b'\\xac', b'=', b'`', b'\\u2011',
                b'\\u2018', b'\\u02d1', b'.', b'\\u02c8', b'\\u02dc', b'~'],
            'Check_segmental': [
                b'\\u03c9', b'\\u03ce', b'\\u021b', b'\\u0219', b'\\xd8',
                b'\\u01ab', b'\\u02b7', b'\\u1d5b', b'\\u2071', b'\\u1d35',
                b'\\u02b8', b'\\u1d64', b'\\u02b0', b'\\u2082', b'\\u02e4',
                b'\\u0261', b'\\u1e55'],
            'Change_capitals': [
                b'U', b'J', b'V', b'C', b'Z', b'K', b'I', b'S', b'N', b'A',
                b'H', b'D', b'O', b'P', b'T', b'R', b'M', b'L', b'E', b'B',
                b'G', b'W', b'Y', b'X', b'F', b'Q', b'\\u0160', b'\\xc4',
                b'\\u012a'],
            'Change_combining': [
                b'\\u0323', b'\\u0306', b'\\u032f', b'\\u0300', b'\\u0301',
                b'\\u0302', b'\\u0303', b'\\u0304', b'\\u0340', b'\\u0325',
                b'\\u0341', b'\\u030c', b'\\u0307', b'\\u0310', b'\\u0332',
                b'\\u031c', b'\\u0327', b'\\u0361', b'\\u0331', b'\\u0330',
                b'\\u030a', b'\\u0344', b'\\u0308'],
            'Change_modifier': [b'\\u02f3', b'\\u02ca']
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
            with open(bName+'.txt', 'w') as file:
                file.write('id, meaning, romanised\n')
                for lexeme in lexemes:
                    file.write(
                        '%s, %s, %s\n' % (
                            lexeme.id, lexeme.meaning, lexeme.romanised))
