import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.production.models.work_session import WorkSession
from apps.production.services.work_session_service import (
    COLOMBIA_TZ,
    force_close,
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

        logger.info("GRACE_HOURS=%sh | now=%s | dry_run=%s", grace_hours, now_utc.isoformat(), dry_run)

        open_sessions = (
            WorkSession.objects.filter(is_closed=False)
            .select_related("work_shift")      
            .order_by("started_at")
        )

        total = open_sessions.count()
        logger.info("Open sessions found: %s", total)

        closed = 0
        skipped = 0
        errors = 0

        for session in open_sessions:
            try:
                expires_at = session_expires_at(session, grace_hours)
                started_local = session.started_at.astimezone(COLOMBIA_TZ)
                expires_local = expires_at.astimezone(COLOMBIA_TZ)

                if now_utc >= expires_at:
                    logger.info(
                        "[EXPIRE] id=%s user=%s started=%s expires=%s editing_finalized=%s",
                        session.id,
                        session.user_id,
                        started_local.strftime("%Y-%m-%d %H:%M"),
                        expires_local.strftime("%Y-%m-%d %H:%M"),
                        session.editing_finalized,
                    )
                    if not dry_run:
                        force_close(session, expires_at)
                    closed += 1
                else:
                    remaining = expires_at - now_utc
                    hours_left = remaining.total_seconds() / 3600
                    logger.info(
                        "[SKIP] id=%s user=%s expires=%s (%.1fh remaining)",
                        session.id,
                        session.user_id,
                        expires_local.strftime("%Y-%m-%d %H:%M"),
                        hours_left,
                    )
                    skipped += 1

            except Exception as exc:
                logger.error("[ERROR] id=%s — %s", session.id, exc)
                errors += 1

        action = "Would close" if dry_run else "Closed"
        log_fn = logger.error if errors else logger.info
        log_fn("%s %s | Skipped %s | Errors %s", action, closed, skipped, errors)
