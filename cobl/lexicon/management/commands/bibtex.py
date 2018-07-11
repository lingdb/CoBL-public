# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from django.core.management import BaseCommand

from cobl.bibtex_import import bibtex_update


class Command(BaseCommand):

    help = "Reads in bibtex data to update the database with."

    def add_arguments(self, parser):
        parser.add_argument('file', nargs='+', type=str)

    def handle(self, *args, **options):
        bibtex_update(options['file'][0])
