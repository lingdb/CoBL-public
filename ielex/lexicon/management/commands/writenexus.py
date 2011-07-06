from optparse import make_option
from django.core.management.base import NoArgsCommand, CommandError
from ielex.lexicon.views import write_nexus

class Command(NoArgsCommand):
    help="""Export a nexus file from the database"""
    requires_model_validation = False
    option_list = NoArgsCommand.option_list + (
            make_option("--language-list", dest="language_list",
                action="store", default="all",
                help="Name of language list [all]"),
            make_option("--meaning-list", dest="meaning_list",
                action="store", default="all",
                help="Name of meaning list [all]"),
            make_option("--unique", dest="unique",
                action="store_true", default=False,
                help="Include unique cognate sets [False]"),
            make_option("--outfile", dest="filename",
                action="store", default=None,
                help="Name of meaning list [all]"),
            )

    def handle(self, **options):
        if options["filename"]:
            fileobj = open(options["filename"], "w")
        else:
            fileobj = self.stdout
        fileobj = write_nexus(fileobj,
            options["language_list"],
            options["meaning_list"],
            set(["L","X"]), # exclude
            "NN", # dialect
            True, # label cognate sets
            options["unique"])
        fileobj.close()
        return

