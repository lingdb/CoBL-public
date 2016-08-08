# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management import BaseCommand

from ielex.lexicon.models import MeaningList, \
                                 LanguageList, \
                                 Lexeme


class Command(BaseCommand):

    help = "Compute statistics for https://github.com/lingdb/CoBL/issues/225"

    def handle(self, *args, **options):
        # Making sure we use `Jena200`
        ml = MeaningList.objects.get(name=MeaningList.DEFAULT)
        # Making sure we use `Current`
        ll = LanguageList.objects.get(name=LanguageList.DEFAULT)
        # Gathering lexemes to work with:
        lexemes = Lexeme.objects.filter(
            meaning__in=ml.meanings.values_list('id', flat=True),
            language__in=ll.languages.values_list('id', flat=True)).all()
        # Calculating:
        self.stdout.write("1: + lex. excl - Not swh")
        for l in lexemes:
            if not l.not_swadesh_term:
                if l.is_excluded_lexeme:
                    self.stdout.write(l.id)
        # is_loan_lexeme no longer available:
        # self.stdout.write("2: + lex .loan - Not swh")
        # for l in lexemes:
        #     if not l.not_swadesh_term:
        #         if l.is_loan_lexeme:
        #             self.stdout.write(l.id)
        # self.stdout.write("3: + lex. loan")
        # for l in lexemes:
        #     if l.is_loan_lexeme:
        #         self.stdout.write(l.id)
        self.stdout.write("4: 2 >= cognate sets - Not swh")
        for l in lexemes:
            if not l.not_swadesh_term:
                if l.cognatejudgement_set.count() >= 2:
                    self.stdout.write(str(l.id))
        self.stdout.write("5: + cog. excl. - Not swh")
        for l in lexemes:
            if not l.not_swadesh_term:
                if l.is_excluded_cognate:
                    self.stdout.write(str(l.id))
        self.stdout.write("6: + cog. loan - Not swh")
        for l in lexemes:
            if not l.not_swadesh_term:
                if l.is_loan_cognate:
                    self.stdout.write(l.id)
        self.stdout.write("\n1: loanword, no loan event in cognate class:")
        for l in lexemes:
            if l.is_loan_cognate:
                for cc in l.cognate_class.all():
                    if not cc.loanword:
                        self.stdout.write('Lexeme %s, cognate class %s.' %
                                          (l.id, cc.id))
        self.stdout.write("\n2: loanword, no cognate class:")
        for l in lexemes:
            if l.is_loan_cognate:
                if l.cognate_class.count() == 0:
                    self.stdout.write(str(l.id))
