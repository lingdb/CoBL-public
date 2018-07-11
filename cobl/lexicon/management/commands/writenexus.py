from optparse import make_option
from os.path import expanduser, expandvars
from cobl.lexicon.views import write_nexus
from cobl.lexicon.models import LanguageList, MeaningList
from cobl.utilities import LexDBManagementCommand


class Command(LexDBManagementCommand):
    help = """Export a nexus file from the database"""
    requires_model_validation = False
    unique_choices = ["all", "limited", "none"]
    dialects = ["MB", "BP", "NN"]
    option_list = (
            make_option(
                "--language-list", dest="language_list",
                action="store", default="all", metavar="NAME",
                help="Name of language list [%s]" % LanguageList.DEFAULT),
            make_option(
                "--meaning-list", dest="meaning_list",
                action="store", default="all", metavar="NAME",
                help="Name of meaning list [%s]" % MeaningList.DEFAULT),
            make_option(
                "--dialect", dest="dialect", choices=dialects,
                action="store", default="NN",
                metavar=("{%s}" % "|".join(dialects)),
                help=("NEXUS dialect: MrBayes, BayesPhylogenies, NeighborNet"
                      " [NN]")),
            make_option(
                "--ascertainment-marker", dest="ascertainment_marker",
                action="store_true", default=False,
                help=("Insert dummy columns for ascertainment correction: "
                      "For each meaning, insert 0 if there is valid 1/0 data, "
                      "and ? if there are only ???")),
            make_option(
                "--outfile", dest="filename",
                action="store", default=None,
                help="Name of destination file [output to screen]"),
            )

    def handle(self, **options):
        if options["filename"]:
            fileobj = open(expanduser(expandvars(options["filename"])), "w")
        else:
            fileobj = self.stdout
        fileobj = write_nexus(
            fileobj,
            options["language_list"],
            options["meaning_list"],
            set(["L", "X"]),  # exclude
            options["dialect"],  # dialect
            True,  # label cognate sets
            options["ascertainment_marker"])['fileobj']
        fileobj.close()
