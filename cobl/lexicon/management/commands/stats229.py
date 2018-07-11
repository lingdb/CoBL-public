# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management import BaseCommand

from cobl.lexicon.models import Lexeme, LanguageList


class Command(BaseCommand):

    help = "Compute statistics for https://github.com/lingdb/CoBL/issues/229"

    def handle(self, *args, **options):
        '''
        Printing all Lexemes from the `Current` LanguageList
        across all meanings, where:
        * at least one LexemeCitation has a reliability of 'X'
        * not_swadesh_term is False
        See https://github.com/lingdb/CoBL/issues/229
        '''
        # Computing lexemes:
        lList = LanguageList.objects.get(name='Current')
        languageIds = lList.languages.values_list('id', flat=True)
        lexemes = Lexeme.objects.filter(language__in=languageIds).all()
        # Printing wanted lexemes:
        for lexeme in lexemes:
            reliabilities = set([lc.reliability for lc
                                 in lexeme.lexemecitation_set.all()])
            if 'X' in reliabilities and not lexeme.not_swadesh_term:
                self.stdout.write(str(lexeme.id))
