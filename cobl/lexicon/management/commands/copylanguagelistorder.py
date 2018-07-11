from optparse import make_option
from django.core.management.base import CommandError
from cobl.lexicon.models import LanguageList, LanguageListOrder
from cobl.utilities import LexDBManagementCommand


class Command(LexDBManagementCommand):
    help = """Reorder TARGET language list to match SOURCE"""
    requires_model_validation = False
    option_list = (
            make_option(
                "-s", "--source-list", dest="copy_from",
                action="store", default="all",
                help="Name of language list to copy order from [all]"),
            make_option(
                "-t", "--target-list", dest="copy_to",
                action="store", default=None,
                help="Name of destination language list"),
            )

    def handle(self, **options):
        # get source list to copy from
        try:
            source_list = LanguageList.objects.get(name=options["copy_from"])
        except LanguageList.DoesNotExist:
            msg = "Source list does not exist. Choices are: %s" % ", ".join(
                    LanguageList.objects.values_list("name", flat=True))
            raise CommandError(msg)

        try:
            target_list = LanguageList.objects.get(name=options["copy_to"])
        except LanguageList.DoesNotExist:
            msg = "Target list does not exist. Choices are: %s" % ", ".join(
                    LanguageList.objects.values_list("name", flat=True))
            raise CommandError(msg)

        # copy languagelistorder from source
        source_list.sequentialize()
        target_list.sequentialize()
        for language in target_list.languages.all():
            llt = LanguageListOrder.objects.get(
                    language=language,
                    language_list=target_list)
            llt.order = LanguageListOrder.objects.get(
                    language=language,
                    language_list=source_list).order + 0.1  # avoid collisions
            llt.save()
