from optparse import make_option, SUPPRESS_HELP
from django.core.management.base import NoArgsCommand, CommandError
from ielex.lexicon.models import LanguageList, LanguageListOrder

class Command(NoArgsCommand):
    help="""Export a nexus file from the database"""
    requires_model_validation = False
    unique_choices = ["all", "limited", "none"]
    option_list = (
            make_option("-l", "--language-list", dest="clone_from",
                action="store", default="all",
                help="Name of language list to clone from [all]"),
            make_option("-n", "--new-name", dest="clone_to",
                action="store", default=None,
                help="Name of new language list"),
            )

    def run_from_argv(self, argv):
        """
        A version of the method from 
        Django-1.3-py2.7.egg/django/core/management/base.py
        with call to handle_default_options disabled
        """
        parser = self.create_parser(argv[0], argv[1])
        options, args = parser.parse_args(argv[2:])
        # handle_default_options(options)
        assert not hasattr(options, "settings")
        assert not hasattr(options, "pythonpath")
        self.execute(*args, **options.__dict__)
        return

    def handle(self, **options):
        # get source list to clone from
        try:
            source_list = LanguageList.objects.get(name=options["clone_from"])
        except LanguageList.DoesNotExist:
            msg = "You can only clone from a language list that "\
                    "already exists. Choices are: %s" % ", ".join(
                    LanguageList.objects.values_list("name", flat=True))
            raise CommandError(msg)

        # make list to clone order to
        dest_list, created = LanguageList.objects.get_or_create(name=options["clone_to"])
        try:
            assert created
        except AssertionError:
            msg = "Language list name %s already exists. Choose another name." % options["clone_to"]
            raise CommandError(msg)

        # copy languagelistorder
        for language in source_list.languages.all().order_by("languagelistorder"):
            dest_list.append(language)

        msg = "Created LanguageList `%s' with %s languages" % (dest_list.name,
                dest_list.languages.count())
        print msg
        return

