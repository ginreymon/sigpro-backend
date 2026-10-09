import json
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.utils.date_utils import to_utc_naive

# Shared by ProductionRecordViewSet and StampingRecordViewSet. The production
# models/services it needs (WorkSession, WorkShiftSnapshot, ModuleDowntime,
# ProductionRecord...) are imported lazily inside the functions, so this module
# has no import-time dependency on `apps.production`.
MANUAL_DURATION_BATCH_DOWNTIME_NAME = 'PRODUCTION RECORD DOWNTIME'


def active_work_session_and_activity(request):
    """
    Resolves the user's open work session and its current active activity
    (or (None, None) if there is none). It is the server's source of truth —
    never trust a work_session_activity that already comes assembled from the
    frontend, because it may have been closed/rotated since that payload was
    built. Shared by production and stamping.
    """
    from apps.production.models import WorkSession

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
    from apps.production.models import WorkShiftSnapshot
    from apps.production.repositories.productivity_repository import ProductivityRepository
    from apps.production.services.work_session_service import shift_start_utc

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

    work_session, activity = active_work_session_and_activity(request)
    indicators = manual_duration_indicators(work_session, activity, tipo_modulo)
    if not indicators:
        raise ValidationError({'duration_seconds': 'No hay una jornada (sesión) activa.'})

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
            duration_seconds=float(duration_seconds),
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
    from apps.production.models.module_downtime import ModuleDowntime
    from apps.production.models.production_record import ProductionRecord

    now = timezone.now()
    elapsed_real_seconds = (now - indicators['period_start']).total_seconds()
    total_duration = duration_seconds + extra_seconds

    if indicators['has_no_records']:
        available_seconds = (
            elapsed_real_seconds
            - indicators['work_break_seconds']
            - indicators['module_downtime_seconds']
            - total_duration
        )
        if available_seconds < 0:
            raise ValidationError({
                'duration_seconds': 'La duración excede el tiempo disponible del turno.'
            })

        shift_start = indicators['period_start']
        start_time = shift_start.replace(year=now.year, month=now.month, day=now.day)
        end_time = record.end_time - timedelta(seconds=total_duration)
    else:
        available_seconds = elapsed_real_seconds - indicators['elapsed_time_max_seconds'] - total_duration
        if available_seconds < 0:
            raise ValidationError({
                'duration_seconds': 'La duración excede el tiempo disponible del turno.'
            })

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
