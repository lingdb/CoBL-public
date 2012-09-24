from __future__ import print_function
from optparse import make_option
from datetime import datetime, timedelta
import sys
from django.core.management.base import NoArgsCommand, CommandError
from django.core.mail import mail_admins
from django.contrib.auth.models import User
from reversion.models import Revision
from ielex.utilities import LexDBManagementCommand
from ielex.lexicon.models import *

class Command(LexDBManagementCommand):
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

    def handle(self, **options):
        if options["dry_run"]:
            io=sys.stdout
        else:
            import StringIO, codecs
            buffer = StringIO.StringIO()
            codecinfo = codecs.lookup("utf8")
            io = codecs.StreamReaderWriter(buffer,
                    codecinfo.streamreader, codecinfo.streamwriter)
        activity_flag = False
        print_report = get_printer(io)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=options["num_days"])
        print_report("== Report period ==")
        print_report("Start:", strftime(start_date))
        print_report("  End:", strftime(end_date))
        print_report()

        # Report logins
        print_report("== Logins ==")
        for user in User.objects.filter(
                last_login__gt=start_date).order_by("last_name"):
            print_report(strftime(user.last_login), strfuser(user))
            activity_flag = True
        print_report()


        # Report database changes
        boring_models = [LanguageListOrder]
        recent_changes = Revision.objects.filter(
                date_created__gt=start_date).order_by("date_created")
        print_report("== Activity report ==")
        for revision in recent_changes:
            timestamp = strftime(revision.date_created)
            user = revision.user
            print_report(timestamp, user)
            for version in revision.version_set.all():
                if version.content_type.model_class() not in boring_models:
                    try:
                        print_report(" ", version.get_type_display(),
                                repr(version.get_object_version().object))
                    except:
                        print_report(" ", version.get_type_display(),
                                "OBJECT UNAVAILABLE")
                    activity_flag = True

        # Send email
        if not options["dry_run"]:
            if activity_flag:
                io.seek(0)
                subject = ("Activity report %s" %
                        strftime(end_date))
                mail_admins(subject, io.read())
            else:
                if options["include_empty"]:
                    subject = ("No activity %s" %
                            strftime(end_date))
                    msg = "No activity from %s to %s" % (strftime(start_date),
                        strftime(end_date))
                    mail_admins(subject, msg)
        return

# standard report formatters

def get_printer(fileobj):
    def printer(*args, **kwargs):
        kwargs["file"] = fileobj
        print(*args, **kwargs)
        return
    return printer

def strfuser(userobj):
    if userobj.last_name:
        return "%s %s (%s)" % (userobj.first_name, userobj.last_name,
                userobj.username)
    else:
        return userobj.username

def strftime(datetimeobj):
    return datetimeobj.strftime("%Y-%m-%d %H:%M:%S")
