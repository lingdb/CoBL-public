from optparse import make_option
from os.path import expanduser, expandvars
from django.core.management.base import NoArgsCommand, CommandError
from ielex.lexicon.views import write_nexus

class Command(NoArgsCommand):
    help="""Export a nexus file from the database"""
    requires_model_validation = False
    unique_choices = ["all", "limited", "none"]
    option_list = NoArgsCommand.option_list + (
            make_option("--language-list", dest="language_list",
                action="store", default="all",
                help="Name of language list [all]"),
            make_option("--meaning-list", dest="meaning_list",
                action="store", default="all",
                help="Name of meaning list [all]"),
            make_option("--unique", dest="unique",
                action="store", type="choice", default=None,
                choices=unique_choices ,
                help=("Include unique cognate sets. Choices: %s" %
                ", ".join(unique_choices))),
            make_option("--outfile", dest="filename",
                action="store", default=None,
                help="Name of destinate filename"),
            )

    def handle(self, **options):
        if options["filename"]:
            fileobj = open(expanduser(expandvars(options["filename"])), "w")
        else:
            fileobj = self.stdout
        if options["unique"] == 'none':
            options["unique"] = False
        fileobj = write_nexus(fileobj,
            options["language_list"],
            options["meaning_list"],
            set(["L","X"]), # exclude
            "NN", # dialect
            True, # label cognate sets
            options["unique"])
        fileobj.close()
        return

