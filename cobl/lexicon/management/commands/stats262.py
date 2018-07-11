# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management import BaseCommand

from cobl.lexicon.models import Language, \
                                 Meaning, \
                                 Lexeme, \
                                 CognateJudgementCitation


class Command(BaseCommand):

    help = "Computes statistics for https://github.com/lingdb/CoBL/issues/262"\
           "\nPossible parameters are: {1, 2, 3} for task number."

    def add_arguments(self, parser):
        parser.add_argument('task', type=int)

    missing_args_message = "Please provide a task number of {1,2,3}."

    def handle(self, *args, **options):
        # Data to work with:
        languageIds = Language.objects.filter(
            languagelist__name='Current').values_list('id', flat=True)
        meaningIds = Meaning.objects.filter(
            meaninglist__name='Jena200').values_list('id', flat=True)
        lexemeIds = Lexeme.objects.filter(
            language_id__in=languageIds,
            meaning_id__in=meaningIds,
            not_swadesh_term=False).values_list('id', flat=True)
        self.stdout.write("Task %s:" % options['task'])
        taskFilter = {1: 'C',  # Doubtful
                      2: 'L',  # Loanword
                      3: 'X'}  # Exclude
        cjcs = CognateJudgementCitation.objects.filter(
            cognate_judgement__lexeme_id__in=lexemeIds,
            reliability=taskFilter[options['task']]).all()
        for cjc in cjcs:
            cj = cjc.cognate_judgement
            self.stdout.write("CognateJudgementCitation %s "
                              "of CognateClass %s "
                              "and Lexeme %s." % (cjc.id,
                                                  cj.cognate_class.id,
                                                  cj.lexeme.id))
