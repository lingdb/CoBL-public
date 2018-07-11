# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management import BaseCommand

from cobl.lexicon.models import LanguageList, \
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

        if options['task'] == 1:
            self.stdout.write('Task 1')
            self.report(self.compute(2, cognateClasses,
                                     meaningIds, languageIds), meaningIds)
        elif options['task'] == 2:
            self.stdout.write('Task 2')
            task1 = self.compute(2, cognateClasses, meaningIds, languageIds)
            task1CCIds = set([c.id for c in task1 if c is not None])
            self.report([c for c in self.compute(
                1, cognateClasses, meaningIds, languageIds)
                if c is not None and c.id not in task1CCIds], meaningIds)
        elif options['task'] == 3:
            self.stdout.write('Task 3')
            unwantedCognateClassIds = set(
                [c.id for c in self.compute(1, cognateClasses,
                                            meaningIds,
                                            languageIds) if c is not None])
            cIdcladeMap = {c.id: c for c in Clade.objects.exclude(
                cladeLevel0=0).all()}
            # Computing ._cognateClasses for each clade:
            for _, clade in cIdcladeMap.items():
                inCladeLanguageIds = set(LanguageClade.objects.filter(
                    clade=clade).values_list('language_id', flat=True))
                lexemes = Lexeme.objects.filter(
                    language_id__in=languageIds & inCladeLanguageIds,
                    meaning_id__in=meaningIds,
                    not_swadesh_term=False).all()
                cognateClassIds = set(CognateJudgement.objects.filter(
                    lexeme__in=lexemes).values_list(
                    'cognate_class_id', flat=True))
                clade._cognateClassIds = set(CognateClass.objects.filter(
                    id__in=cognateClassIds - unwantedCognateClassIds,
                    root_form='').order_by('id').values_list('id', flat=True))
            # Removing cognate class IDs we don't want:
            for _, clade in cIdcladeMap.items():
                cogIdCounts = {cId: 0 for cId in clade._cognateClassIds}
                childIds = clade.queryChildren().values_list('id', flat=True)
                for childId in childIds:
                    child = cIdcladeMap[childId]
                    for cId in child._cognateClassIds:
                        if cId in cogIdCounts:
                            cogIdCounts[cId] += 1
                # Setting ._cognateClassIds for current clade:
                clade._cognateClassIds = set([cId for cId, count
                                              in cogIdCounts.items()
                                              if count != 1])
                # Updating children:
                for childId in childIds:
                    child = cIdcladeMap[childId]
                    child._cognateClassIds = child._cognateClassIds & \
                        set([cId for cId, count
                             in cogIdCounts.items()
                             if count == 1])
            # Creating .txt files:
            for _, clade in cIdcladeMap.items():
                # Grouping by meaning:
                meaningMarkdowns = {}
                for c in clade._cognateClassIds:
                    s = '- [ ] cog. class '\
                        '[%s](http://cobl.info/cognate/%s/)' % (c, c)
                    meanings = Meaning.objects.filter(
                        lexeme__cognate_class=c,
                        lexeme__language_id__in=languageIds,
                        lexeme__not_swadesh_term=False,
                        id__in=meaningIds).distinct().all()
                    s += ''.join([
                        ' = meaning [%s](http://cobl.info/meaning/%s/)' %
                        (m.gloss, m.gloss) for m in meanings])
                    for m in meanings:
                        if m.gloss not in meaningMarkdowns:
                            meaningMarkdowns[m.gloss] = []
                        meaningMarkdowns[m.gloss].append(s)
                # Composing markdown:
                markdown = []
                for k in sorted(meaningMarkdowns.keys()):
                    markdown += meaningMarkdowns[k]
                # Writing if content:
                if len(markdown) > 0:
                    fname = '/tmp/%s.txt' % clade.taxonsetName
                    self.stdout.write("Writing file '%s'." % fname)
                    with open(fname, 'w') as f:
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
                    language_id__in=languageIds,
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

    def report(self, cognateClasses, meaningIds):
        # Print given cognateClasses:
        for cognateClass in cognateClasses:
            if cognateClass is None:
                continue
            lexemeIds = CognateJudgement.objects.filter(
                cognate_class_id=cognateClass.id).values_list(
                'lexeme_id', flat=True)
            meaningNames = Meaning.objects.filter(
                lexeme__id__in=lexemeIds,
                id__in=meaningIds).distinct().values_list('gloss', flat=True)
            meaningNames = ', '.join(['"%s"' % m for m in meaningNames])
            self.stdout.write("Cognate set id: %s "
                              "meanings: %s branches: %s" %
                              (cognateClass.id,
                               meaningNames,
                               cognateClass.bNames))
