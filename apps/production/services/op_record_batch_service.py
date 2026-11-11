import json
import math
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.production.models import ProductionRecord, WorkSession, WorkShiftSnapshot
from apps.production.models.module_downtime import ModuleDowntime
from apps.production.models.work_session_activity_employee import WorkSessionActivityEmployee
from apps.production.repositories.productivity_repository import ProductivityRepository
from apps.production.services.work_session_service import shift_start_utc
from core.utils.date_utils import to_utc_naive

# Shared by ProductionRecordViewSet and StampingRecordViewSet. It lives in
# `apps.production` (stamping depends on production, never the reverse).
MANUAL_DURATION_BATCH_DOWNTIME_NAME = 'PRODUCTION RECORD DOWNTIME'


def active_work_session_and_activity(request):
    """
    Resolves the user's open work session and its current active activity
    (or (None, None) if there is none). It is the server's source of truth —
    never trust a work_session_activity that already comes assembled from the
    frontend, because it may have been closed/rotated since that payload was
    built. Shared by production and stamping.
    """
    work_session = WorkSession.objects.filter(user=request.user, is_closed=False).first()
    if not work_session:
        return None, None

    activity = work_session.get_active_activity()
    return work_session, activity


def manual_duration_indicators(work_session, activity, tipo_modulo: str):
    """
    Shift time indicators for `activity`, used to validate duration_seconds
    against the shift. None if there is no active session/activity.
    tipo_modulo: 'production' or 'stamping' (see ProductivityRepository).
    """
    if not work_session or not activity:
        return None

    shift_snapshot = (
        WorkShiftSnapshot.objects.filter(work_session=work_session)
        .order_by("-id")
        .first()
    )
    shift_start_time = (
        shift_snapshot.start_time if shift_snapshot else work_session.work_shift.start_time
    )
    shift_end_time = (
        shift_snapshot.end_time if shift_snapshot else work_session.work_shift.end_time
    )

    fecha_inicio = to_utc_naive(shift_start_utc(work_session, shift_start_time, shift_end_time))
    return ProductivityRepository.get_tiempos_operacion_modulo(
        fecha_inicio,
        activity.module_id,
        work_session.work_shift_id,
        tipo_modulo=tipo_modulo,
    )


def manual_duration_budget_seconds(indicators: dict, now) -> float:
    """
    Seconds of the shift that a manual-duration batch can still consume
    (before subtracting the batch's own duration). Single source of truth
    shared by the save validation (create_manual_duration_batch_downtime) and
    the simulation (simulate_manual_duration_batch), so they cannot diverge.

    has_no_records=True:  elapsed_real - work_break - module_downtime
    has_no_records=False: elapsed_real - elapsed_time_max
    """
    elapsed_real_seconds = (now - indicators['period_start']).total_seconds()
    if indicators['has_no_records']:
        return (
            elapsed_real_seconds
            - indicators['work_break_seconds']
            - indicators['module_downtime_seconds']
        )
    return elapsed_real_seconds - indicators['elapsed_time_max_seconds']


def _activity_employee_count(activity) -> float:
    """
    Weighted employee count of the activity. Mirrors dbo.fn_empleados_actividad
    / dbo.fn_peso_empleado: sum over active employees of 0.5 (apprentice) or
    worked_minutes_per_hour / 60 (NULL = 60), each weight rounded to 4 decimals.
    """
    total = Decimal('0')
    rows = WorkSessionActivityEmployee.objects.filter(
        work_session_activity=activity, is_active=True,
    ).values_list('is_apprentice', 'worked_minutes_per_hour')
    for is_apprentice, minutes in rows:
        weight = Decimal('0.5') if is_apprentice else Decimal(minutes if minutes is not None else 60) / Decimal(60)
        total += weight.quantize(Decimal('0.0001'))
    return float(total)


# Hard cap of the efficiency (%) a manual-duration batch may produce. Single
# source of truth: simulate returns it and save enforces it.
MAX_EFFICIENCY_PCT = 100.0

# Smallest duration the simulation advertises (the frontend input works in minutes).
MIN_DURATION_SECONDS = 60

# Quantity fields that make a record "carry units" (production uses all three,
# stamping only completed_quantity).
_QUANTITY_FIELDS = ('completed_quantity', 'rejected_quantity', 'scrap_quantity')


def validate_batch_records(records) -> None:
    """
    Rejects a batch with omitted quantities or duplicated records (the same
    payload twice), so the efficiency is computed over exactly the units the
    user intended. The batch may mix several references / production orders.
    """
    seen = set()
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise ValidationError({'records': f'El registro {index} no es válido.'})
        try:
            units = sum(Decimal(str(record.get(field) or 0)) for field in _QUANTITY_FIELDS)
        except InvalidOperation:
            raise ValidationError({'records': f'El registro {index} tiene cantidades no numéricas.'})
        if units <= 0:
            raise ValidationError({'records': f'El registro {index} no tiene cantidades registradas.'})
        key = json.dumps(record, sort_keys=True, default=str)
        if key in seen:
            raise ValidationError({'records': f'El registro {index} está duplicado.'})
        seen.add(key)


def _batch_target(lines, duration_seconds, employee_count: float, tipo_modulo: str):
    """
    Target units of the batch with the same formulas as the SQL functions.

    lines: one dict {sam, completed, total} per record (each record carries
    its own reference/SKU SAM; `total` is completed+scrap+rejected for
    production, completed for stamping). The batch has ONE duration, so it is
    distributed across the records in proportion to their standard time
    (completed * sam): a record never gets the whole time just because it is
    first, and a slow reference weighs more than a fast one.

    per record with sam > 0, net = duration * (completed*sam) / sum(completed*sam):
      production (fn_eficiencia_periodo_produccion): target = net * employees / (60 * sam)
      stamping (fn_eficiencia_periodo_estampacion):  target = net / 3600 * tasks_per_hour * employees,
                                                     tasks_per_hour = round(60 / sam, 2)
    record without SAM: target = total (same fallback as the SQL).
    """
    standard = sum(line['sam'] * line['completed'] for line in lines if line['sam'] > 0)
    target = 0.0
    for line in lines:
        if line['sam'] <= 0:
            target += line['total']
        elif standard > 0:
            net = duration_seconds * (line['sam'] * line['completed']) / standard
            if tipo_modulo == 'stamping':
                tasks_per_hour = float(Decimal(60 / line['sam']).quantize(Decimal('0.01')))
                target += net / 3600.0 * tasks_per_hour * employee_count
            else:
                target += net * employee_count / (60.0 * line['sam'])
    return target


def _batch_efficiency(lines, duration_seconds, employee_count: float, tipo_modulo: str, rounded: bool = True):
    """
    Efficiency (%) of the whole batch = sum(total) * 100 / target (see
    _batch_target). Returns None only when there is no duration to simulate;
    otherwise 0 like the SQL when the target is not positive. rounded=False
    gives the exact value, used to compare against MAX_EFFICIENCY_PCT.
    """
    if not duration_seconds or duration_seconds <= 0:
        return None

    total = sum(line['total'] for line in lines)
    target = _batch_target(lines, duration_seconds, employee_count, tipo_modulo)
    if target <= 0:
        return 0.0
    value = total * 100.0 / target
    return round(value, 2) if rounded else value


def min_duration_for_max_efficiency(lines, employee_count: float, tipo_modulo: str) -> float:
    """
    Smallest duration (seconds) whose efficiency does not exceed
    MAX_EFFICIENCY_PCT. The target is linear in the duration:
    target(D) = fixed + per_second * D, where `fixed` is the target of the
    records without SAM (independent of time). Solving
    total * 100 / target(D) <= MAX gives
    D >= (total * 100 / MAX - fixed) / per_second. 0 when time cannot lower the
    efficiency (no per-second target, e.g. no employees or no SAM).
    """
    total = sum(line['total'] for line in lines)
    fixed = _batch_target(lines, 0.0, employee_count, tipo_modulo)
    per_second = _batch_target(lines, 1.0, employee_count, tipo_modulo) - fixed
    if per_second <= 0 or total <= 0:
        return 0.0
    return max(0.0, (total * 100.0 / MAX_EFFICIENCY_PCT - fixed) / per_second)


def simulate_manual_duration_batch(request, tipo_modulo: str, lines, extra_available_seconds: float = 0):
    """
    Read-only counterpart of perform_manual_duration_batch (nothing is saved).
    Returns the payload of POST .../manual-duration-batch/simulate/:
    {min_duration_seconds, max_duration_seconds, efficiency, max_efficiency}.

    min_duration_seconds is the smallest duration that keeps the efficiency at
    or below max_efficiency (min_duration_for_max_efficiency, floored at
    MIN_DURATION_SECONDS) - the same rule perform_manual_duration_batch
    enforces on save.

    max_duration_seconds is the same budget the save validation uses
    (manual_duration_budget_seconds) minus extra_available_seconds, floored at
    0; None (with efficiency None) when there is no active session/activity.
    lines: see _batch_efficiency (built by the view from the request records).

    Deviation note: extra seconds (stamping additional_times) are NOT added to
    the net time of the efficiency: fn_eficiencia_periodo_estampacion subtracts
    additional_time_minutes from the interval, i.e. they are non-productive.
    """
    validate_batch_records(request.data.get('records') or [])
    work_session, activity = active_work_session_and_activity(request)
    indicators = manual_duration_indicators(work_session, activity, tipo_modulo)
    result = {
        'min_duration_seconds': MIN_DURATION_SECONDS,
        'max_duration_seconds': None,
        'efficiency': None,
        'max_efficiency': MAX_EFFICIENCY_PCT,
    }
    if not indicators:
        return result

    employee_count = _activity_employee_count(activity)
    result['min_duration_seconds'] = max(
        MIN_DURATION_SECONDS,
        math.ceil(round(min_duration_for_max_efficiency(lines, employee_count, tipo_modulo), 6)),
    )
    budget = manual_duration_budget_seconds(indicators, timezone.now())
    result['max_duration_seconds'] = max(0.0, budget - extra_available_seconds)

    try:
        duration_seconds = float(request.data.get('duration_seconds'))
    except (TypeError, ValueError):
        return result
    result['efficiency'] = _batch_efficiency(lines, duration_seconds, employee_count, tipo_modulo)
    return result


def perform_manual_duration_batch(view, request, tipo_modulo: str, extra_available_seconds: float = 0):
    """
    Shared body of POST .../manual-duration-batch/ for
    ProductionRecordViewSet and StampingRecordViewSet.

    Payload: { "records": [<same shape as the regular create() POST>, ...],
                "duration_seconds": <seconds of the whole batch, one or more records> }

    duration_seconds covers the entire batch (not each individual record): it
    is validated once against the shift and then each record is saved exactly
    like the view serializer's regular create() (all-or-nothing inside a
    transaction). It also creates a single ModuleDowntime covering that
    duration, linked to the first record of the batch (see
    create_manual_duration_batch_downtime). The response is the list of all
    saved records (same serializer.data as a regular create()), each one with
    the batch's duration_seconds.

    extra_available_seconds: additional time that the caller already computed
    outside this function and that is added to duration_seconds both for the
    shift budget validation and for the downtime span (start_time/end_time)
    (see create_manual_duration_batch_downtime). Production does not use it
    (defaults to 0); stamping uses it for the standard time of the batch's
    additional_times (see StampingRecordViewSet.manual_duration_batch).
    """
    records = request.data.get('records')
    if not records or not isinstance(records, list):
        raise ValidationError({'records': 'Debe incluir al menos un registro.'})

    duration_seconds = request.data.get('duration_seconds')
    if duration_seconds is None:
        raise ValidationError({'duration_seconds': 'Este campo es requerido.'})
    try:
        duration_seconds = float(duration_seconds)
    except (TypeError, ValueError):
        raise ValidationError({'duration_seconds': 'La duración debe ser un número.'})
    if duration_seconds <= 0:
        raise ValidationError({'duration_seconds': 'La duración debe ser mayor que cero.'})

    validate_batch_records(records)

    work_session, activity = active_work_session_and_activity(request)
    indicators = manual_duration_indicators(work_session, activity, tipo_modulo)
    if not indicators:
        raise ValidationError({'duration_seconds': 'No hay una jornada (sesión) activa.'})

    # Same rule the simulation advertises: the duration cannot produce an
    # efficiency above MAX_EFFICIENCY_PCT. Exact (unrounded) comparison.
    lines = view.get_batch_efficiency_lines(records)
    efficiency = _batch_efficiency(
        lines, duration_seconds, _activity_employee_count(activity), tipo_modulo, rounded=False,
    )
    if efficiency is not None and efficiency > MAX_EFFICIENCY_PCT + 1e-9:
        raise ValidationError({
            'duration_seconds': f'La duración produce una eficiencia superior al {MAX_EFFICIENCY_PCT:.2f} % permitido.'
        })

    with transaction.atomic():
        created = []
        # The work_session_activity carried by each record of the batch was
        # captured in the frontend when it was queued (in-memory store), which
        # may have been open for a while — by the time the batch is confirmed
        # that activity may already be closed (activity rotation, end of
        # shift, etc). The server is the source of truth: every record is
        # forced onto the activity that is actually active now, and if
        # serializer.create() rotates it mid-batch (SKU change), the
        # following records follow that rotation.
        current_activity_id = activity.id if activity else None
        first_instance = None
        record_ids = []
        for record in records:
            if current_activity_id is not None:
                record = {**record, 'work_session_activity': current_activity_id}

            serializer = view.get_serializer(data=record)
            serializer.is_valid(raise_exception=True)
            view.perform_create(serializer)
            current_activity_id = serializer.instance.work_session_activity_id
            if first_instance is None:
                first_instance = serializer.instance
            record_ids.append(serializer.instance.id)

            data = dict(serializer.data)
            data['duration_seconds'] = duration_seconds
            created.append(data)

        create_manual_duration_batch_downtime(
            record=first_instance,
            record_ids=record_ids,
            indicators=indicators,
            duration_seconds=duration_seconds,
            user=request.user,
            extra_seconds=extra_available_seconds,
        )

    return Response(created, status=201)


def create_manual_duration_batch_downtime(
    *, record, record_ids, indicators: dict, duration_seconds: float, user, extra_seconds: float = 0,
):
    """
    Creates the ModuleDowntime that covers the manual duration of a whole batch
    (manual-duration-batch): there is a single downtime per batch, linked only
    to the first created record (production_record or stamping_record,
    depending on the type of `record`). custom_reason stores
    {"record_ids": [...]} with the ids of ALL the records in the batch
    (serialized to JSON), not just the linked one —
    ModuleDowntime.save() derives `name` from custom_reason automatically.

    extra_seconds: additional time that is added to duration_seconds both for
    the shift budget validation and for the downtime's own span
    (start_time/end_time) — the standard time of additional_times also
    occupied the shift, so the downtime must cover
    duration_seconds + extra_seconds, not just duration_seconds. Production
    always passes 0 (no behavior change); stamping passes the standard time
    of the batch's additional_times (see perform_manual_duration_batch).

    The start_time/end_time values depend on `indicators`
    (see manual_duration_indicators) and on total_duration = duration_seconds + extra_seconds:

    has_no_records=True:
        validates (now - period_start) - work_break_seconds - module_downtime_seconds - total_duration >= 0
        start_time = shift start time with the current date (today)
        end_time   = record.end_time - total_duration

    has_no_records=False:
        validates (now - period_start) - elapsed_time_max_seconds - total_duration >= 0
        start_time = period_start + elapsed_time_max_seconds (end of the previous record)
        end_time   = record.end_time - total_duration

    If the corresponding validation fails, raises ValidationError.

    Reusable by production and stamping — the correct ModuleDowntime FK
    (production_record/stamping_record) is resolved from the type of `record`.
    """
    now = timezone.now()
    total_duration = duration_seconds + extra_seconds
    available_seconds = manual_duration_budget_seconds(indicators, now) - total_duration

    if available_seconds < 0:
        raise ValidationError({
            'duration_seconds': 'La duración excede el tiempo disponible del turno.'
        })

    if indicators['has_no_records']:
        shift_start = indicators['period_start']
        start_time = shift_start.replace(year=now.year, month=now.month, day=now.day)
        end_time = record.end_time - timedelta(seconds=total_duration)
    else:
        end_time = record.end_time - timedelta(seconds=total_duration)
        start_time = indicators['period_start'] + timedelta(seconds=indicators['elapsed_time_max_seconds'])

    link_field = "production_record" if isinstance(record, ProductionRecord) else "stamping_record"

    return ModuleDowntime.objects.create(
        module=record.work_session_activity.module,
        name=MANUAL_DURATION_BATCH_DOWNTIME_NAME,
        custom_reason=json.dumps({'record_ids': record_ids}),
        start_time=start_time,
        end_time=end_time,
        resumed_at=None,
        created_by=user,
        updated_by=user,
        **{link_field: record},
    )
