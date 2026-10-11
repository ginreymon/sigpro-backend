import math

from django.db import transaction
from django.utils import timezone

from apps.production.models import WorkBreakRecord
from apps.production.repositories.work_session_repository import WorkSessionActivityRepository
from apps.production.services.exceptions import SessionRuleError


def _already_paused_error(activity) -> SessionRuleError:
    detail = "La actividad ya está pausada. Debes reanudarla para continuar."
    active_break = activity.active_break

    if active_break and active_break.end_time:
        remaining_minutes = math.ceil(
            (active_break.end_time - timezone.now()).total_seconds() / 60
        )
        if remaining_minutes > 0:
            detail = f"La actividad está pausada. Faltan {remaining_minutes} minuto(s) para reanudar."
        else:
            detail = "El tiempo de pausa ya terminó. Reanuda la actividad para continuar."

    return SessionRuleError({"detail": detail})


def _require_open_activity(activity) -> None:
    if not activity.is_active:
        raise SessionRuleError({"detail": "La actividad no está activa."})

    if activity.work_session.is_closed:
        raise SessionRuleError({"detail": "La jornada (sesión) está cerrada."})


def pause(activity, user, *, work_break_id, custom_reason, work_break_minutes, auto_resume):
    """
    Pauses `activity`. With a work_break type the break is open until /resume/;
    with a custom reason and `work_break_minutes` (stamping) the end is known up
    front. `auto_resume=True` registers the break already resolved
    (end_time == resumed_at) instead of waiting for a resume.

    The order of the checks is part of the contract (messages the UI shows).
    """
    _require_open_activity(activity)

    if activity.is_paused:
        raise _already_paused_error(activity)

    if not work_break_id and not custom_reason:
        raise SessionRuleError({"detail": "Debe indicar un tipo de pausa o un motivo personalizado."})

    if auto_resume and not work_break_id and work_break_minutes is None:
        raise SessionRuleError(
            {"detail": "Debe indicar work_break_minutes para calcular el auto-resume del motivo personalizado."}
        )

    if work_break_minutes is not None:
        try:
            work_break_minutes = int(work_break_minutes)
        except (TypeError, ValueError):
            raise SessionRuleError({"detail": "Los minutos deben ser un número entero."})
        if work_break_minutes < 1:
            raise SessionRuleError({"detail": "Los minutos deben ser mayores a 0."})

    now = timezone.now()
    break_kwargs = {
        "work_session_activity": activity,
        "start_time": now,
        "created_by": user,
        "updated_by": user,
    }

    if work_break_id:
        work_break = WorkSessionActivityRepository.find_work_break(work_break_id)
        if work_break is None:
            raise SessionRuleError({"detail": "El tipo de pausa no existe."}, status_code=404)
        break_kwargs["work_break"] = work_break
    else:
        break_kwargs["custom_reason"] = custom_reason.strip()

    record = WorkBreakRecord(**break_kwargs)

    if work_break_minutes is not None and not work_break_id:
        record.end_time = now + timezone.timedelta(minutes=work_break_minutes)

    with transaction.atomic():
        WorkSessionActivityRepository.save_break_record(record)

        if auto_resume:
            record.resumed_at = record.end_time
            WorkSessionActivityRepository.save_break_record(record)

    return record


def resume(activity) -> WorkBreakRecord:
    """Resumes the open break of `activity`."""
    _require_open_activity(activity)

    active_break = activity.active_break

    if not active_break:
        raise SessionRuleError({"detail": "La actividad no está pausada."})

    now = timezone.now()
    active_break.resumed_at = now

    if not active_break.work_break_id:
        active_break.end_time = now

    WorkSessionActivityRepository.save_break_record(active_break)

    return active_break
