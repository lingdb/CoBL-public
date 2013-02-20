from __future__ import print_function
from optparse import make_option
from ielex.lexicon.models import LanguageList, MeaningList
from ielex.utilities import LexDBManagementCommand

class Command(LexDBManagementCommand):
    help="""Export a nexus file from the database"""
    requires_model_validation = False
    option_list = tuple()

    def handle(self, **options):
        print("Language lists:")
        for ll in LanguageList.objects.all():
            print("  %s [%s]" % (ll.name, ll.languages.count()))
        print("Meaning lists:")
        for ml in MeaningList.objects.all():
            print("  %s [%s]" % (ml.name, len(ml.meaning_id_list)))
        return

