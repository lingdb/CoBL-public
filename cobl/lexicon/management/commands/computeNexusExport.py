# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

from time import strftime

from django.core.management import BaseCommand

from cobl.lexicon.models import NexusExport
from cobl.lexicon.views import write_nexus


class Command(BaseCommand):

    help = "Computes nexus export for a given id."\
           "\nThis command is also issued by NexusExport.forkComputation."

    def handle(self, *args, **options):
        # Data to work with:
        for export in NexusExport.objects.filter(_exportData=None).all():
            assert export.pending, "Export must be pending for computation."
            # Calculating the export:
            print('Calculating NexusExport %s.' % export.id)

            data = write_nexus(**export.getSettings())

            export.exportData = data['exportData']
            export.constraintsData = "\n".join([data['cladeMemberships'],
                                                data['computeCalibrations']])
            export.exportBEAUti = data['exportBEAUti']
            export.exportTableData = data['exportTableData']
            export.exportMatrix = data['exportMatrix']
            export.save()
            print('Done.', strftime("%Y-%m-%d %H:%M:%S"))
