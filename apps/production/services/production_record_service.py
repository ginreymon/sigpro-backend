import json
from datetime import timedelta

from django.utils import timezone
from rest_framework.exceptions import ValidationError


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
    (ver _manual_duration_indicators):

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
