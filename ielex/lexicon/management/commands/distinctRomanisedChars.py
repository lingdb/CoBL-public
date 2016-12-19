# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from django.core.management import BaseCommand
from ielex.lexicon.models import Lexeme


class Command(BaseCommand):

    help = "Produces a list of distinct chars " \
           "in romanised fields in the database."

    def handle(self, *args, **options):
        chars = set()
        for romanised in Lexeme.objects.values_list('romanised', flat=True):
            chars |= set(romanised)
        print('chars:', ' '.join(sorted(chars)))
