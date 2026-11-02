from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.production.repositories.work_session_repository import WorkSessionRepository
from apps.production.services.employee_assignment_service import (
    sync_module_assignees,
    validate_employee_conflicts,
    validate_employees_active,
)
from apps.production.services.exceptions import SessionRuleError
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


def shift_start_utc(session, shift_start_time, shift_end_time) -> datetime:
    """
    Local (Colombia) shift start for `session`, using its own start date.

    Overnight shift only (end_time <= start_time, crosses midnight): if the
    session started in the early-morning tail of the shift (before
    start_time), the shift actually began the day before, so the date rolls
    back by one day.

    A same-day shift never rolls back, even if the session started a few
    minutes before start_time (early clock-in) — otherwise that would wrongly
    push the shift start a full day earlier.

    Returns a UTC-aware datetime.
    """
    started_local = session.started_at.astimezone(COLOMBIA_TZ)
    session_date = started_local.date()

    shift_start_local = datetime.combine(session_date, shift_start_time, tzinfo=COLOMBIA_TZ)

    is_overnight_shift = shift_end_time <= shift_start_time
    if is_overnight_shift and shift_start_local > started_local:
        shift_start_local -= timedelta(days=1)

    return shift_start_local


def session_core_module_id(session):
    """core_module_id (process) of the session's active activity, or None if it has none/unassigned location."""
    activity = session.get_active_activity()
    if not activity or not activity.module.location_id:
        return None
    return activity.module.location.core_module_id


def finalize_expired_session(session, expires_at: datetime) -> None:
    """
    Closes a session that exceeded its shift window and leaves it finalized.

    The session ends at expires_at (shift end + grace) and editing_finalized is
    set: records are captured hourly, so a session that is closed by expiry
    instead of by the user must lock the hourly editing, which is what the flag
    does in the frontend and in the SQL functions. WorkSession.close_session
    (manual close) does not finalize.
    """
    with transaction.atomic():
        activity = session.get_active_activity()
        if activity:
            activity.close()

        ended_at = max(expires_at, session.started_at)

        session.ended_at = ended_at
        session.is_closed = True
        session.editing_finalized = True
        session.save(update_fields=["ended_at", "is_closed", "editing_finalized"])


def open_session(user, target_module_id, create):
    """
    Opens a new session for `user`. Any session the user still has open is
    closed first, unless it belongs to a different process (core module) than
    the one being started — then the user must close it explicitly.

    `create` persists the new session (serializer.save) inside the same
    transaction and lock as the check.
    """
    with transaction.atomic():
        active = WorkSessionRepository.lock_open_session_of(user)
        if active:
            if target_module_id:
                target_module = WorkSessionRepository.find_module_with_location(target_module_id)
                target_core_module_id = (
                    target_module.location.core_module_id
                    if target_module and target_module.location_id
                    else None
                )
                if str(session_core_module_id(active)) != str(target_core_module_id):
                    active_activity = active.get_active_activity()
                    active_module_name = active_activity.module.name if active_activity else None
                    if active_module_name:
                        message = (
                            f'Ya tienes una jornada (sesión) activa en el módulo "{active_module_name}". '
                            "Ciérrala antes de iniciar una nueva."
                        )
                    else:
                        message = (
                            "Ya tienes una jornada (sesión) activa en otro proceso. "
                            "Ciérrala antes de iniciar una nueva."
                        )
                    raise ValidationError(message)
            active.close_session()
        return create()


def close(session):
    """Closes `session` and returns it reloaded with its related data."""
    if session.is_closed:
        raise SessionRuleError({"detail": "Session already closed"})

    session.close_session()
    return WorkSessionRepository.get_detail(session.pk)


def close_active_session(user):
    """
    Closes the user's open session manually (no expiry finalization, same as
    close()), or returns None when there is none. The row lock makes the
    check and the close atomic.
    """
    with transaction.atomic():
        session = WorkSessionRepository.lock_open_session_of(user)
        return close(session) if session else None


def get_active_session(user, core_module_id=None):
    """
    The user's open session, or None. Also None when it belongs to another
    process than `core_module_id`, or when it already expired (an expired session
    is force-closed here).
    """
    session = WorkSessionRepository.find_open_session_of(user)

    if not session:
        return None

    if core_module_id and str(session_core_module_id(session)) != str(core_module_id):
        return None

    expires_at = session_expires_at(session, get_grace_hours())

    if timezone.now() >= expires_at:
        finalize_expired_session(session, expires_at)
        return None

    return session


def rotate_activity(session_id, user, read_input):
    """
    Closes the current activity of the session and opens a new one on the same
    module (used when the SKU, the employees or the OP change but the module
    does not). `read_input()` returns (employee_ids, apprentice_ids) — it is a
    callable so the input is validated after the session checks, as before.

    An expired session is force-closed and that close IS committed; the error
    is raised only after the transaction ends.
    """
    expired = False

    with transaction.atomic():
        session = WorkSessionRepository.lock_by_id(session_id)

        if session.is_closed:
            raise SessionRuleError({"detail": "La jornada (sesión) está cerrada."})

        expires_at = session_expires_at(session, get_grace_hours())

        if timezone.now() >= expires_at:
            finalize_expired_session(session, expires_at)
            expired = True
        else:
            employee_ids, apprentice_ids = read_input()

            current_activity = session.get_active_activity()

            if employee_ids is not None:
                resolved_employee_ids = employee_ids
            elif current_activity:
                resolved_employee_ids = list(
                    current_activity.employee_snapshots.values_list("employee_id", flat=True)
                )
            else:
                resolved_employee_ids = []

            validate_employees_active(resolved_employee_ids)
            validate_employee_conflicts(resolved_employee_ids, current_activity)

            try:
                new_activity = session.restart_activity(
                    employee_ids=employee_ids,
                    created_by=user,
                    apprentice_ids=apprentice_ids,
                )
            except LookupError as error:
                raise SessionRuleError({"detail": str(error)})

            sync_module_assignees(new_activity.module, user)

    if expired:
        raise SessionRuleError(["La jornada (sesión) ha expirado."])

    return new_activity