# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management import BaseCommand

from ielex.lexicon.models import LanguageList, \
                                 MeaningList, \
                                 Meaning, \
                                 Lexeme, \
                                 CognateClass, \
                                 CognateJudgement, \
                                 LanguageClade, \
                                 Clade


class Command(BaseCommand):

    help = "Computes statistics for https://github.com/lingdb/CoBL/issues/236"\
           "\nPossible parameters are: {1, 2, 3} for task number."

    def add_arguments(self, parser):
        parser.add_argument('task', type=int)

    missing_args_message = "Please provide a task number of {1,2,3}."

    def handle(self, *args, **options):
        # Data to work with:
        current = LanguageList.objects.get(name='Current')
        jena200 = MeaningList.objects.get(name='Jena200')
        languageIds = set(current.languages.values_list('id', flat=True))
        meaningIds = jena200.meanings.values_list('id', flat=True)
        lexemeIds = Lexeme.objects.filter(
            language_id__in=languageIds,
            meaning_id__in=meaningIds).values_list('id', flat=True)
        cognateClassIds = CognateJudgement.objects.filter(
            lexeme_id__in=lexemeIds).values_list(
            'cognate_class_id', flat=True)
        cognateClasses = CognateClass.objects.filter(
            id__in=cognateClassIds,
            root_form='').all()  # Only without root_form is wanted.

        if(options['task'] == 1):
            self.stdout.write('Task 1')
            self.report(self.compute(2, cognateClasses,
                                     meaningIds, languageIds))
        elif(options['task'] == 2):
            self.stdout.write('Task 2')
            self.report(self.compute(1, cognateClasses,
                                     meaningIds, languageIds))
        elif(options['task'] == 3):
            self.stdout.write('Task 3')
            unwantedCognateClassIds = set(
                [c.id for c in self.compute(1, cognateClasses,
                                            meaningIds,
                                            languageIds) if c is not None])
            for clade in Clade.objects.exclude(cladeLevel0=0).all():
                subSelection = [('cladeLevel0', clade.cladeLevel0),
                                ('cladeLevel1', clade.cladeLevel1),
                                ('cladeLevel2', clade.cladeLevel2),
                                ('cladeLevel3', clade.cladeLevel3)]
                subSelection = {k: v for k, v in subSelection if v != 0}
                unwantedLanguageIds = set(LanguageClade.objects.filter(
                    clade_id__in=Clade.objects.filter(
                        **subSelection).exclude(
                        id=clade.id).values_list(
                        'id', flat=True)).values_list(
                    'language_id', flat=True))
                inCladeLanguageIds = set(LanguageClade.objects.filter(
                    clade=clade).values_list('language_id', flat=True))
                wantedLanguageIds = languageIds & (inCladeLanguageIds -
                                                   unwantedLanguageIds)
                lexemes = Lexeme.objects.filter(
                    language_id__in=wantedLanguageIds,
                    meaning_id__in=meaningIds,
                    not_swadesh_term=False).all()
                cognateClassIds = set(CognateJudgement.objects.filter(
                    lexeme__in=lexemes).values_list(
                    'cognate_class_id', flat=True))
                cognateClasses = CognateClass.objects.filter(
                    id__in=cognateClassIds - unwantedCognateClassIds,
                    root_form='').order_by('id').values_list('id', flat=True)
                fname = '/tmp/%s.md' % clade.taxonsetName
                self.stdout.write("Writing file '%s'." % fname)
                with open(fname, 'w') as f:
                    markdown = []
                    for c in cognateClasses:
                        s = '- [ ] cog. class '\
                            '[%s](http://cobl.info/cognate/%s/)' % (c, c)
                        meanings = Meaning.objects.filter(
                            lexeme__cognate_class=c,
                            lexeme__not_swadesh_term=False).distinct().all()
                        s += ''.join([
                            ' = meaning [%s](http://cobl.info/meaning/%s/)' %
                            (m.gloss, m.gloss) for m in meanings])
                        markdown.append(s)
                    f.write("\n".join(markdown)+"\n")

    def compute(self, lowerBranchBound,
                cognateClasses, meaningIds, languageIds):
        # The computation we want to perform twice
        for cognateClass in cognateClasses:
            lexemeIds = CognateJudgement.objects.filter(
                cognate_class_id=cognateClass.id).values_list(
                'lexeme_id', flat=True)
            # Need to investigate lexemes:
            cladeNamesSet = set()
            for lexeme in Lexeme.objects.filter(
                    id__in=lexemeIds,
                    meaning_id__in=meaningIds).all():
                # Need to investigate clades:
                clades = Clade.objects.filter(
                    id__in=LanguageClade.objects.filter(
                        language_id=lexeme.language_id,
                        language_id__in=languageIds).values_list(
                        'clade_id', flat=True),
                    cladeLevel1=0).exclude(
                    cladeLevel0=0  # Ignore PIE
                    ).all()
                if len(clades) > 0:
                    cladeNamesSet.add(', '.join([
                        c.cladeName for c in clades]))
            # Yield interesting clades:
            if len(cladeNamesSet) > lowerBranchBound:
                cognateClass.bNames = ', '.join('"%s"' % n for
                                                n in cladeNamesSet)
                yield(cognateClass)
        yield(None)  # EOG

    def report(self, cognateClasses):
        # Print given cognateClasses:
        for cognateClass in cognateClasses:
            if cognateClass is None:
                continue
            lexemeIds = CognateJudgement.objects.filter(
                cognate_class_id=cognateClass.id).values_list(
                'lexeme_id', flat=True)
            meaningIds = Lexeme.objects.filter(
                id__in=lexemeIds).values_list('meaning_id', flat=True)
            meaningNames = Meaning.objects.filter(
                id__in=meaningIds).values_list('gloss', flat=True)
            meaningNames = ', '.join(['"%s"' % m for m in meaningNames])
            self.stdout.write("Cognate set id: %s "
                              "meanings: %s branches: %s" %
                              (cognateClass.id,
                               meaningNames,
                               cognateClass.bNames))
