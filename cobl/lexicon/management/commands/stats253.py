# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from collections import defaultdict

from django.core.management import BaseCommand
from cobl.lexicon.models import CognateClass, LanguageList, MeaningList


class Command(BaseCommand):

    help = "Computes statistics for https://github.com/lingdb/CoBL/issues/380"

    def handle(self, *args, **options):
        languageList = LanguageList.objects.get(name=LanguageList.DEFAULT)
        meaningList = MeaningList.objects.get(name=MeaningList.DEFAULT)
        cognateClasses = CognateClass.objects.filter(
            lexeme__language__in=languageList.languages.all(),
            lexeme__meaning__in=meaningList.meanings.all()
        )
        buckets = defaultdict(int)
        for cognateClass in cognateClasses.all():
            for symbol in cognateClass.root_form:
                buckets[symbol] += 1
        print('Symbol, Unicode, Occurences')
        for k, v in buckets.items():
            print("%s, %s, %s" % (k, k.encode('unicode_escape'), v))
