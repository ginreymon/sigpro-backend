from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils import timezone

from core.models.app_setting import AppSetting

COLOMBIA_TZ = ZoneInfo("America/Bogota")
DEFAULT_GRACE_HOURS = 8


def get_grace_hours() -> int:
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


def session_expires_at(session, grace_hours: int) -> datetime:
    """
    Expiry = (session date in local time) + shift.end_time + grace_hours.
    Night shift: if shift end_time <= session start_time, advance end_time by 1 day.
    Returns UTC-aware datetime.
    """
    started_local = session.started_at.astimezone(COLOMBIA_TZ)
    session_date = started_local.date()

    shift_end_local = datetime.combine(
        session_date, session.work_shift.end_time, tzinfo=COLOMBIA_TZ
    )

    if shift_end_local <= started_local:
        shift_end_local += timedelta(days=1)

    return shift_end_local + timedelta(hours=grace_hours)


def session_core_module_id(session):
    """core_module_id (process) of the session's active activity, or None if it has none/unassigned location."""
    activity = session.get_active_activity()
    if not activity or not activity.module.location_id:
        return None
    return activity.module.location.core_module_id


def force_close(session, expires_at: datetime) -> None:
    """
    Closes a session using expires_at as ended_at.
    Used for sessions that exceeded their shift window.
    """
    with transaction.atomic():
        activity = session.get_active_activity()
        if activity:
            activity.close()

        ended_at = max(expires_at, session.started_at)

        session.ended_at = ended_at
        session.total_time = ended_at - session.started_at
        session.is_closed = True
        session.editing_finalized = True
        session.save(update_fields=["ended_at", "total_time", "is_closed", "editing_finalized"])
