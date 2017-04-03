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
    tmpl = "Sending monthly report to %s"

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
        day_before = now - timedelta(minutes=1)
        # initialise db query conditions for next report date
        daily_report_due = Q(next_report_date__lt=now)
        daily_report_not_scheduled = Q(next_report_date__isnull=True)
        # filter query results
        daily = Profile.objects.filter(daily_report_due | daily_report_not_scheduled)
        # get rows where report preference is daily
        daily = daily.filter(reports_allowed="daily")
        daily = daily.filter(user__date_joined__lt=day_before)
        daily_sent = 0
        # send email to all users who choose daily reports
        for profile in daily:
            # send email only if there were checks for current user
            if num_pinged_checks(profile) > 0:
                self.stdout.write(self.tmpl % profile.user.email)
                profile.send_daily_report()
                daily_sent += 1

        # get time stamp for week before to
        # ensure user only gets email at the earliest at
        # least 1 week after subscribing
        week_before = now - timedelta(days=7)
        # initialise db query conditions for next report date
        week_report_due = Q(next_report_date__lt=now)
        week_report_not_scheduled = Q(next_report_date__isnull=True)
        # filter query results
        weekly = Profile.objects.filter(week_report_due | week_report_not_scheduled)
        # get rows where report preference is weekly
        weekly = weekly.filter(reports_allowed="weekly")
        weekly = weekly.filter(user__date_joined__lt=week_before)
        weekly_sent = 0
        # send email to all users who choose weekly reports
        for profile in weekly:
            # send email only if there were checks for current user
            if num_pinged_checks(profile) > 0:
                self.stdout.write(self.tmpl % profile.user.email)
                profile.send_weekly_report()
                weekly_sent += 1

        # get time stamp for month before to
        # ensure user only gets email at the earliest at
        # least 1 month after subscribing
        month_before = now - timedelta(days=30)
        # initialise db query conditions for next report date
        month_report_due = Q(next_report_date__lt=now)
        month_report_not_scheduled = Q(next_report_date__isnull=True)
        # filter query results
        monthly = Profile.objects.filter(month_report_due | month_report_not_scheduled)
        # get rows where report preference is monthly
        monthly = monthly.filter(reports_allowed="monthly")
        monthly = monthly.filter(user__date_joined__lt=month_before)
        monthly_sent = 0
        # send email to all users who choose monthly reports
        for profile in monthly:
            # send email only if there were checks for current user
            if num_pinged_checks(profile) > 0:
                self.stdout.write(self.tmpl % profile.user.email)
                profile.send_monthly_report()
                monthly_sent += 1

        return daily_sent, weekly_sent, monthly_sent

    def handle(self, *args, **options):
        """
        Method to 
        """
        if not options["loop"]:
            return ("Sent %d daily reports\n %d weekly reports\n" +
                    "%d monthly reports" % self.handle_one_run())

        self.stdout.write("sendreports is now running")
        while True:
            self.handle_one_run()

            formatted = timezone.now().isoformat()
            self.stdout.write("-- MARK %s --" % formatted)

            time.sleep(300)
