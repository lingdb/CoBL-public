from __future__ import print_function
from optparse import make_option
import datetime
from django.core.management.base import NoArgsCommand, CommandError
from reversion.models import Revision

class Command(NoArgsCommand):
    help="""Report the changes to the database over the previous N days"""
    option_list = (
            make_option("-n", "--dry-run", dest="dry_run",
                action="store_true", default=False,
                help="Report daily summary to stdout"),
            make_option("-e", "--no-empty", dest="include_empty",
                action="store_false", default=True,
                help="Suppress reports when there have been no changes"),
            make_option("-d", "--num-days", dest="num_days",
                action="store", default=1, type=int,
                metavar="N",
                help="Report the activity for the previous N days"),
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
        # TODO make a filter so that this report doesn't tell too much about
        # e.g. LanguageListOrder changes
        start_date = datetime.datetime.now() - datetime.timedelta(
                days=options["num_days"])
        recent_changes = Revision.objects.filter(
                date_created__gt=start_date).order_by("-id")
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
                print(timestamp, user)
                for version in revision.version_set.all():
                    try:
                        print(" ", version.get_type_display(),
                                repr(version.get_object_version().object))
                    except:
                        print(" ", version.get_type_display(),
                                "OBJECT UNAVAILABLE")

        return

