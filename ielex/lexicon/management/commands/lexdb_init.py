from django.core.management.base import NoArgsCommand
from ielex.lexicon.models import LanguageList, MeaningList
from ielex.utilities import LexDBManagementCommand

class Command(LexDBManagementCommand):
    help="Create LanguageList and MeaningList objects in an empty database"
    option_list = tuple()

    def handle(self, **options):
        LanguageList.objects.get_or_create(name=LanguageList.DEFAULT)
        MeaningList.objects.get_or_create(name=MeaningList.DEFAULT)
        return
