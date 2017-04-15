import logging
import time

from concurrent.futures import ThreadPoolExecutor
from django.core.management.base import BaseCommand
from django.db import connection
from datetime import timedelta
from django.utils import timezone
from hc.api.models import Check

executor = ThreadPoolExecutor(max_workers=10)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sends UP/DOWN email alerts'

    def handle_many(self):
        """ Send alerts for many checks simultaneously. """
        query = Check.objects.filter(user__isnull=False).select_related("user")
        nag_interval_seconds = sum(int(x) * 60 ** i for i,x in enumerate(reversed(str(Check.nag_interval.split(":")))))
        # time_array = str(Check.nag_interval).split(":")
        # nag_interval_seconds = float(time_array[0]) * 3600 + float(time_array[1]) * 60 + float(time_array[2])

        due_nag_alerts = Check.last_alert + timedelta(seconds=nag_interval_seconds)

        now = timezone.now()
        going_down = query.filter(alert_after__lt=now, status="up")
        going_up = query.filter(alert_after__gt=now, status="down")

        going_nag = query.filter(due_nag_alerts__gt=now, status="nag")

        # Don't combine this in one query so Postgres can query using index:
        checks = list(going_down.iterator()) + list(going_up.iterator()) + list(going_nag.iterator())
        if not checks:
            return False

        futures = [executor.submit(self.handle_one, check) for check in checks]
        for future in futures:
            future.result()

        return True

    def handle_one(self, check):
        """ Send an alert for a single check.

        Return True if an appropriate check was selected and processed.
        Return False if no checks need to be processed.

        """

        # Save the new status. If sendalerts crashes,
        # it won't process this check again.
        check.status = check.get_status()
        check.save()

        tmpl = "\nSending alert, status=%s, code=%s\n"
        self.stdout.write(tmpl % (check.status, check.code))
        errors = check.send_alert()
        for ch, error in errors:
            self.stdout.write("ERROR: %s %s %s\n" % (ch.kind, ch.value, error))

        connection.close()
        return True

    def handle(self, *args, **options):
        self.stdout.write("sendalerts is now running")

        ticks = 0
        while True:
            if self.handle_many():
                ticks = 1
            else:
                ticks += 1

            time.sleep(1)
            if ticks % 60 == 0:
                formatted = timezone.now().isoformat()
                self.stdout.write("-- MARK %s --" % formatted)
