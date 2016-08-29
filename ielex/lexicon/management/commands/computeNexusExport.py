# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import StringIO
from time import strftime

from django.core.management import BaseCommand

from ielex.lexicon.models import NexusExport
from ielex.lexicon.views import write_nexus


class Command(BaseCommand):

    help = "Computes nexus export for a given id."\
           "\nThis command is also issued by NexusExport.forkComputation."

    def handle(self, *args, **options):
        # Data to work with:
        for export in NexusExport.objects.filter(_exportData=None).all():
            assert export.pending, "Export must be pending for computation."
            # Calculating the export:
            print('Calculating NexusExport %s.' % export.id)
            output = StringIO.StringIO()

            data = write_nexus(fileobj=output, **export.getSettings())

            export.exportData = output.getvalue()
            export.constraintsData = "\n".join([data['cladeMemberships'],
                                                data['computeCalibrations']])
            export.save()
            output.close()
            print('Done.', strftime("%Y-%m-%d %H:%M:%S"))
