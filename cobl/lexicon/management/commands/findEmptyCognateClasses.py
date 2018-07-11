# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from django.core.management import BaseCommand

from cobl.lexicon.models import CognateClass


class Command(BaseCommand):

    help = "Compiles a list of cognate classes without lexemes."

    def handle(self, *args, **options):
        emptyCCs = 0
        for cc in CognateClass.objects.order_by('id').all():
            if cc.lexeme_set.count() == 0:
                print("http://cobl.info/cognate/%s/" % (cc.id))
                emptyCCs += 1
        print('Found empty cognate classes: %s/%s' %
              (emptyCCs, CognateClass.objects.count()))
