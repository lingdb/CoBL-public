from django.core.management.base import NoArgsCommand
from ielex.lexicon.models import LanguageList, MeaningList

class Command(NoArgsCommand):
    help="Create LanguageList and MeaningList objects in an empty database"
    option_list = tuple()

    def run_from_argv(self, argv):
        """
        A version of the method from
        Django-1.3-py2.7.egg/django/core/management/base.py
        with call to `handle_default_options` disabled in order to
        suppress unwanted default options.
        """
        parser = self.create_parser(argv[0], argv[1])
        options, args = parser.parse_args(argv[2:])
        # handle_default_options(options)
        assert not hasattr(options, "settings")
        assert not hasattr(options, "pythonpath")
        self.execute(*args, **options.__dict__)
        return

    def handle(self, **options):
        LanguageList.objects.get_or_create(name=LanguageList.DEFAULT)
        MeaningList.objects.get_or_create(name=MeaningList.DEFAULT)
        return
