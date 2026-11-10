import logging

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.production.models.work_session import WorkSession
from apps.production.services.work_session_service import (
    COLOMBIA_TZ,
    finalize_expired_session,
    get_grace_hours,
    session_expires_at,
)

logger = logging.getLogger("production.close_expired_sessions")


class Command(BaseCommand):
    help = "Auto-close work sessions that exceeded shift end time + GRACE_HOURS extra hours."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview sessions to close without making changes.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        now_utc = timezone.now()
        grace_hours = get_grace_hours()

        open_sessions = (
            WorkSession.objects.filter(is_closed=False)
            .select_related("work_shift")
            .order_by("started_at")
        )

        reviewed = closed = skipped = errors = 0

        for session in open_sessions:
            reviewed += 1
            try:
                expires_at = session_expires_at(session, grace_hours)

                if now_utc < expires_at:
                    skipped += 1
                    continue

                logger.info(
                    "[EXPIRE] id=%s user=%s started=%s expires=%s editing_finalized=%s",
                    session.id,
                    session.user_id,
                    session.started_at.astimezone(COLOMBIA_TZ).strftime("%Y-%m-%d %H:%M"),
                    expires_at.astimezone(COLOMBIA_TZ).strftime("%Y-%m-%d %H:%M"),
                    session.editing_finalized,
                )
                # Locked + re-checked inside: False means someone else closed it first.
                if dry_run or finalize_expired_session(session, expires_at):
                    closed += 1
                else:
                    skipped += 1

            except Exception:
                logger.exception("[ERROR] id=%s", session.id)
                errors += 1

        summary = "%s | grace=%sh | reviewed=%s closed=%s skipped=%s errors=%s" % (
            "DRY-RUN" if dry_run else "DONE",
            grace_hours,
            reviewed,
            closed,
            skipped,
            errors,
        )
        (logger.error if errors else logger.info)(summary)
        self.stdout.write(summary)

        if errors:
            raise CommandError(f"{errors} session(s) failed to close.")
