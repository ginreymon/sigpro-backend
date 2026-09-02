import json
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.utils.date_utils import to_utc_naive

MANUAL_DURATION_BATCH_DOWNTIME_NAME = 'PRODUCTION RECORD DOWNTIME'


def active_work_session_and_activity(request):
    """
    Resuelve la jornada (sesión) abierta del usuario y su actividad activa
    actual (o (None, None) si no hay ninguna). Es la fuente de verdad del
    servidor — nunca hay que confiar en un work_session_activity que venga
    ya armado desde el frontend, porque puede haberse cerrado/rotado desde
    que se armó ese payload. Compartido por producción y estampación.
    """
    from apps.production.models import WorkSession

    work_session = WorkSession.objects.filter(user=request.user, is_closed=False).first()
    if not work_session:
        return None, None

    activity = work_session.get_active_activity()
    return work_session, activity


def manual_duration_indicators(work_session, activity, tipo_modulo: str):
    """
    Indicadores de tiempo del turno para `activity`, usados para validar
    duration_seconds contra el turno. None si no hay jornada/actividad activa.
    tipo_modulo: 'production' o 'stamping' (ver ProductivityRepository).
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


def perform_manual_duration_batch(view, request, tipo_modulo: str):
    """
    Cuerpo compartido de POST .../manual-duration-batch/ para
    ProductionRecordViewSet y StampingRecordViewSet.

    Payload: { "records": [<mismo shape que POST del create() normal>, ...],
                "duration_seconds": <segundos del lote completo, uno o más registros> }

    duration_seconds cubre el lote entero (no cada registro individual): se
    valida una sola vez contra el turno y luego se guarda cada registro
    exactamente como el create() normal del serializer del view (todo-o-nada
    dentro de una transacción). Además crea un único ModuleDowntime que
    cubre esa duración, enlazado al primer registro del lote (ver
    create_manual_duration_batch_downtime). La respuesta es la lista de
    todos los registros guardados (mismo serializer.data que un create()
    normal), cada uno con el duration_seconds del lote.
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
        # El work_session_activity que trae cada registro del lote se
        # capturó en el frontend al encolarse (store en memoria), que puede
        # llevar rato abierto — para cuando se confirma el lote esa
        # actividad puede ya estar cerrada (rotación de actividad, fin de
        # turno, etc). El servidor es la fuente de verdad: todos los
        # registros se fuerzan a la actividad realmente activa ahora, y si
        # el serializer.create() la rota a mitad de lote (cambio de SKU),
        # los siguientes registros siguen esa rotación.
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
        )

    return Response(created, status=201)


def create_manual_duration_batch_downtime(*, record, record_ids, indicators: dict, duration_seconds: float, user):
    """
    Crea el ModuleDowntime que cubre la duración manual de todo un lote
    (manual-duration-batch): por lote hay un solo downtime, enlazado
    únicamente al primer registro creado (production_record o
    stamping_record, según el tipo de `record`). custom_reason guarda
    {"record_ids": [...]} con los ids de TODOS los registros del lote
    (serializado a JSON), no solo el del registro enlazado —
    ModuleDowntime.save() deriva `name` de custom_reason automáticamente.

    Los tiempos start_time/end_time dependen de `indicators`
    (ver manual_duration_indicators):

    has_no_records=True:
        se valida (now - period_start) - work_break_seconds - module_downtime_seconds - duration_seconds >= 0
        start_time = hora de inicio del turno con la fecha actual (hoy)
        end_time   = record.end_time - duration_seconds

    has_no_records=False:
        se valida (now - period_start) - elapsed_time_max_seconds - duration_seconds >= 0
        end_time   = record.end_time
        start_time = record.end_time - duration_seconds

    Si la validación correspondiente falla, lanza ValidationError.

    Reutilizable por producción y estampación — el link FK correcto de
    ModuleDowntime (production_record/stamping_record) se resuelve según
    el tipo de `record`.
    """
    from apps.production.models.module_downtime import ModuleDowntime
    from apps.production.models.production_record import ProductionRecord

    now = timezone.now()
    elapsed_real_seconds = (now - indicators['period_start']).total_seconds()

    if indicators['has_no_records']:
        available_seconds = (
            elapsed_real_seconds
            - indicators['work_break_seconds']
            - indicators['module_downtime_seconds']
            - duration_seconds
        )
        if available_seconds < 0:
            raise ValidationError({
                'duration_seconds': 'La duración excede el tiempo disponible del turno.'
            })

        shift_start = indicators['period_start']
        start_time = shift_start.replace(year=now.year, month=now.month, day=now.day)
        end_time = record.end_time - timedelta(seconds=duration_seconds)
    else:
        available_seconds = elapsed_real_seconds - indicators['elapsed_time_max_seconds'] - duration_seconds
        if available_seconds < 0:
            raise ValidationError({
                'duration_seconds': 'La duración excede el tiempo disponible del turno.'
            })

        end_time = record.end_time
        start_time = record.end_time - timedelta(seconds=duration_seconds)

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


def validate_manual_duration_budget(indicators: dict, duration_seconds: float) -> None:
    """
    Rejects a manual-duration entry that claims more time than has actually
    elapsed in the shift, net of breaks/downtime (and, once there are prior
    records, net of the elapsed time those records already cover).

    has_no_records:  (now - period_start) - work_break_seconds - module_downtime_seconds - duration_seconds >= 0
    otherwise:       (now - elapsed_time_max_seconds) - duration_seconds > 0

    Raises ValidationError when the budget is exceeded.
    """
    elapsed_real_seconds = (timezone.now() - indicators['period_start']).total_seconds()

    if indicators['has_no_records']:
        available_seconds = (
            elapsed_real_seconds
            - indicators['work_break_seconds']
            - indicators['module_downtime_seconds']
            - duration_seconds
        )
        is_valid = available_seconds >= 0
    else:
        remaining_seconds = elapsed_real_seconds - indicators['elapsed_time_max_seconds']
        available_seconds = remaining_seconds - duration_seconds
        is_valid = available_seconds > 0

    if not is_valid:
        raise ValidationError({
            'duration_seconds': 'La duración excede el tiempo disponible del turno.'
        })
