# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import StringIO

from django.core.management import BaseCommand

from ielex.lexicon.models import NexusExport
from ielex.lexicon.views import write_nexus


class Command(BaseCommand):

    help = "Computes nexus export for a given id."\
           "\nThis command is also issued by NexusExport.forkComputation."

    def add_arguments(self, parser):
        parser.add_argument('exportId', type=int)

    missing_args_message = "Please provide the ID of "\
                           "a NexusExport datbase entry."

    def handle(self, *args, **options):
        # Data to work with:
        try:
            export = NexusExport.objects.get(id=options['exportId'])
        except NexusExport.DoesNotExist:
            self.stderr.write("Export %s does not exist in the database." %
                              options['exportId'])
        assert export.pending, "Export must be pending for computation."
        # Calculating the export:
        self.stdout.write('Calculating NexusExport %s.' % export.id)
        output = StringIO.StringIO()

        write_nexus(fileobj=output, **export.getSettings())

        export.setExportData(output.getvalue())
        output.close()
        self.stdout.write('Done.')
