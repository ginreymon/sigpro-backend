from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.production.models.work_session import WorkSession
from core.models.app_setting import AppSetting

COLOMBIA_TZ = ZoneInfo("America/Bogota")
DEFAULT_GRACE_HOURS = 8


def _get_grace_hours() -> int:
    try:
        value = (
            AppSetting.objects.filter(key="GRACE_HOURS")
            .values_list("value", flat=True)
            .first()
        )
        if value is not None:
            return int(value)
    except (ValueError, TypeError):
        pass
    return DEFAULT_GRACE_HOURS


def _session_expires_at(session: WorkSession, grace_hours: int) -> datetime:
    """
    Expiry = (session date in local time) + shift.end_time + grace_hours.
    If shift end_time <= session start_time (night shift), advance end_time by 1 day.
    Returns UTC-aware datetime.
    """
    started_local = session.started_at.astimezone(COLOMBIA_TZ)
    session_date = started_local.date()

    shift_end_local = datetime.combine(
        session_date, session.work_shift.end_time, tzinfo=COLOMBIA_TZ
    )

    # Night shift: end_time is next calendar day
    if shift_end_local <= started_local:
        shift_end_local += timedelta(days=1)

    return shift_end_local + timedelta(hours=grace_hours)


def _force_close(session: WorkSession, expires_at: datetime) -> None:
    """
    Closes a session using expires_at as the official ended_at.
    Handles sessions that may already have editing_finalized=True but is_closed=False.
    """
    with transaction.atomic():
        # Close any open activity first
        activity = session.get_active_activity()
        if activity:
            activity.close()

        # Use expires_at as ended_at — more accurate than closing at now()
        # Guard: never set ended_at before started_at
        ended_at = max(expires_at, session.started_at)

        session.ended_at = ended_at
        session.total_time = ended_at - session.started_at
        session.is_closed = True
        session.editing_finalized = True
        session.save(update_fields=["ended_at", "total_time", "is_closed", "editing_finalized"])


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
        grace_hours = _get_grace_hours()

        self.stdout.write(
            f"GRACE_HOURS={grace_hours}h | now={now_utc.isoformat()} | dry_run={dry_run}"
        )

        open_sessions = (
            WorkSession.objects.filter(is_closed=False)
            .select_related("work_shift")
            .order_by("started_at")
        )

        total = open_sessions.count()
        self.stdout.write(f"Open sessions found: {total}")

        closed = 0
        skipped = 0
        errors = 0

        for session in open_sessions:
            try:
                expires_at = _session_expires_at(session, grace_hours)
                started_local = session.started_at.astimezone(COLOMBIA_TZ)
                expires_local = expires_at.astimezone(COLOMBIA_TZ)

                if now_utc >= expires_at:
                    self.stdout.write(
                        f"  [EXPIRE] id={session.id} user={session.user_id} "
                        f"started={started_local.strftime('%Y-%m-%d %H:%M')} "
                        f"expires={expires_local.strftime('%Y-%m-%d %H:%M')} "
                        f"editing_finalized={session.editing_finalized}"
                    )
                    if not dry_run:
                        _force_close(session, expires_at)
                    closed += 1
                else:
                    remaining = expires_at - now_utc
                    hours_left = remaining.total_seconds() / 3600
                    self.stdout.write(
                        f"  [SKIP]   id={session.id} user={session.user_id} "
                        f"expires={expires_local.strftime('%Y-%m-%d %H:%M')} "
                        f"({hours_left:.1f}h remaining)"
                    )
                    skipped += 1

            except Exception as exc:
                self.stderr.write(
                    self.style.ERROR(f"  [ERROR]  id={session.id} — {exc}")
                )
                errors += 1

        action = "Would close" if dry_run else "Closed"
        summary = f"{action} {closed} | Skipped {skipped} | Errors {errors}"
        style = self.style.ERROR if errors else self.style.SUCCESS
        self.stdout.write(style(summary))
