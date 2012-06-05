from __future__ import print_function
from optparse import make_option
from datetime import datetime, timedelta
import sys
from StringIO import StringIO
from django.core.management.base import NoArgsCommand, CommandError
from django.core.mail import mail_admins
from reversion.models import Revision
from lexicon.models import *

class Command(NoArgsCommand):
    help="""Report the changes to the database over the previous N days"""
    option_list = (
            make_option("-d", "--dry-run", dest="dry_run",
                action="store_true", default=False,
                help="Report daily summary to stdout "\
                "[default: email it to admins]"),
            make_option("-e", "--no-empty", dest="include_empty",
                action="store_false", default=True,
                help="Suppress reports when there have been no changes "\
                "[default: show empty]"),
            make_option("-n", "--num-days", dest="num_days",
                action="store", default=1, type=int,
                metavar="N",
                help="Report the activity for the previous N days "\
                "[default: 1]"),
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
        if options["dry_run"]:
            fileobj=sys.stdout
        else:
            fileobj=StringIO()
        boring_models = [LanguageListOrder]
        start_date = datetime.now() - timedelta(days=options["num_days"])
        recent_changes = Revision.objects.filter(
                date_created__gt=start_date).order_by("date_created")
        if recent_changes or options["include_empty"]:
            for revision in recent_changes:
                timestamp = revision.date_created.strftime(
                        "%Y-%m-%d %H:%M:%S")
                user = revision.user
                if user.last_name:
                    username = "%s %s (%s)" % (user.first_name, user.last_name,
                            user.username)
                else:
                    username = user.username
                print(timestamp, user, file=fileobj)
                for version in revision.version_set.all():
                    if version.content_type.model_class() not in boring_models:
                        try:
                            print(" ", version.get_type_display(),
                                    repr(version.get_object_version().object),
                                    file=fileobj)
                        except:
                            print(" ", version.get_type_display(),
                                    "OBJECT UNAVAILABLE", file=fileobj)
        if not options["dry_run"]:
            fileobj.seek(0)
            subject = "Daily activity report %s"
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            mail_admins(subject, fileobj.read())
        return

