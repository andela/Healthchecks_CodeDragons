from datetime import timedelta
import time

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from hc.accounts.models import Profile
from hc.api.models import Check


def num_pinged_checks(profile):
    q = Check.objects.filter(user_id=profile.user.id,)
    q = q.filter(last_ping__isnull=False)
    return q.count()


class Command(BaseCommand):
    help = 'Send due monthly reports'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loop',
            action='store_true',
            dest='loop',
            default=False,
            help='Keep running indefinitely in a 300 second wait loop',
        )

    def handle_one_run(self):
        """
        Method to send emails for daily, weekly or monthly
        based on user preference. Method is background worker.
        """
        # get current time

        now = timezone.now()

        # get time stamp for day before to
        # ensure user only gets email at the earliest at
        # least 1 day after subscribing
        number_of_days = {
            "daily": 1,
            "weekly": 7,
            "monthly": 30
        }

        sent_list = []

        for item in number_of_days.keys():

            period_before = now - timedelta(days=number_of_days[item])
            # initialise db query conditions for next report date
            report_due = Q(next_report_date__lt=now)
            report_not_scheduled = Q(next_report_date__isnull=True)
            # filter query results
            report_period = Profile.objects.filter(report_due | report_not_scheduled)
            # get rows depending on report preference
            report_period = report_period.filter(reports_allowed=item)
            report_period = report_period.filter(user__date_joined__lt=period_before)
            sent = 0
            # send email to all users who chose current report type
            for profile in report_period:
                # send email only if there were checks for current user
                if num_pinged_checks(profile) > 0:
                    # terminal output for current report type
                    report_tmpl = "Sending " + item + " report to %s"
                    self.stdout.write(report_tmpl % profile.user.email)
                    profile.send_email_report(number_of_days[item], item)
                    sent += 1
            
            sent_list.append(sent)       

        return sent_list

    def handle(self, *args, **options):
        """
        Method to control frequency of background worker
        """
        if not options["loop"]:
            # configure return statement based on report type
            return "Sent %d daily reports %d weekly reports and %d monthly reports" \
                   % self.handle_one_run()[0], self.handle_one_run()[1], self.handle_one_run()[2]

        self.stdout.write("sendreports is now running")
        while True:
            self.handle_one_run()

            formatted = timezone.now().isoformat()
            self.stdout.write("-- MARK %s --" % formatted)

            time.sleep(30)
