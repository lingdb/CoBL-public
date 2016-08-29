# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import StringIO

from django.core.management import BaseCommand

from ielex.lexicon.models import NexusExport
from ielex.lexicon.views import write_nexus


class Command(BaseCommand):

    help = "Computes nexus export for a given id."\
           "\nThis command is also issued by NexusExport.forkComputation."

    def handle(self, *args, **options):
        # Data to work with:
        exports = NexusExport.objects.filter(exportData=None).all()
        for export in exports:
            assert export.pending, "Export must be pending for computation."
            # Calculating the export:
            print('Calculating NexusExport %s.' % export.id)
            output = StringIO.StringIO()

            data = write_nexus(fileobj=output, **export.getSettings())

            print(data['computeCalibrations'])

            export.setExportData(output.getvalue())
            output.close()
            print('Done.')
