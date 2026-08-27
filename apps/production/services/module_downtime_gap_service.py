"""
Servicio compartido entre producción y estampación para el flujo de
"registro con duración manual" (start_time = now - duración, end_time = now)
y la generación automática del ModuleDowntime que cubre el hueco previo.

Usado por:
    - apps.production.serializers.production_record_manual_serializer
    - apps.stamping.serializers.stamping_record_manual_serializer

Regla clave: los huecos autogenerados NUNCA se solapan entre sí dentro de
una misma jornada. Cada nuevo hueco arranca exactamente donde terminó lo
último cubierto (producción, estampación o paro) y termina donde empieza
el nuevo registro. Así, cuando se hacen varios registros manuales seguidos
en la misma jornada, sus paros de módulo se van sumando correctamente en
fn_paro_modulo_segundos (cada uno enlazado por record_id, sin solape de
fechas que pudiera hacer que se contaran dos veces).

Si la duración indicada por el usuario retrocede más allá del último punto
ya cubierto (es decir, se solaparía con algo ya registrado), se rechaza con
un ValidationError indicando la duración máxima disponible.
"""
from datetime import timedelta

from django.db.models import Max
from django.db.models.functions import Coalesce
from rest_framework.exceptions import ValidationError

from apps.production.models.module_downtime import ModuleDowntime

GAP_REASON_TEXT = "Tiempo no registrado"


def _last_covered_point(
    *, module, work_session, before, exclude_production_id=None, exclude_stamping_id=None
):
    """
    Último instante ya cubierto (producción, estampación o paro de módulo)
    para este módulo dentro de la jornada `work_session`, antes de `before`.
    Si no hay nada todavía, se usa el inicio de la jornada.

    Se consultan las tres fuentes porque un módulo puede alternar entre
    registros de producción y de estampación (y paros reales) dentro de la
    misma jornada; el punto cubierto es el máximo de las tres.
    """
    # Imports diferidos para evitar dependencias circulares entre apps.
    from apps.production.models.production_record import ProductionRecord
    from apps.stamping.models.stamping_record import StampingRecord

    session_start = work_session.started_at

    last_production_end = ProductionRecord.objects.filter(
        work_session_activity__work_session=work_session,
        work_session_activity__module=module,
        end_time__isnull=False,
        end_time__lte=before,
    )
    if exclude_production_id is not None:
        last_production_end = last_production_end.exclude(pk=exclude_production_id)
    last_production_end = last_production_end.aggregate(m=Max("end_time"))["m"]

    last_stamping_end = StampingRecord.objects.filter(
        work_session_activity__work_session=work_session,
        work_session_activity__module=module,
        end_time__isnull=False,
        end_time__lte=before,
    )
    if exclude_stamping_id is not None:
        last_stamping_end = last_stamping_end.exclude(pk=exclude_stamping_id)
    last_stamping_end = last_stamping_end.aggregate(m=Max("end_time"))["m"]

    last_downtime_end = ModuleDowntime.objects.filter(
        module=module,
        start_time__gte=session_start,
        start_time__lt=before,
    ).annotate(
        effective_end=Coalesce("resumed_at", "end_time"),
    ).aggregate(m=Max("effective_end"))["m"]

    candidates = [d for d in (last_production_end, last_stamping_end, last_downtime_end) if d]
    return max(candidates) if candidates else session_start


def apply_manual_duration(*, record, work_session, duration_seconds, link_field):
    """
    Ajusta start_time/end_time de `record` (ProductionRecord o
    StampingRecord recién creado — llega con start_time = end_time = now,
    puesto por auto_now_add) según la duración indicada manualmente, y crea
    el ModuleDowntime que cubre el hueco previo (si existe), enlazado al
    registro por FK exacto — no por solape de fechas.

    Parámetros:
        record            Instancia ya guardada (ProductionRecord o
                           StampingRecord).
        work_session       Jornada activa (record.work_session_activity.work_session).
        duration_seconds  Duración en segundos indicada por el usuario.
        link_field        "production_record" o "stamping_record" — el FK
                           de ModuleDowntime que corresponde a este tipo de
                           registro.

    Lanza ValidationError si la duración se solapa con tiempo ya cubierto.
    """
    module = record.work_session_activity.module
    now = record.start_time

    computed_start = now - timedelta(seconds=duration_seconds)

    last_covered = _last_covered_point(
        module=module,
        work_session=work_session,
        before=now,
        exclude_production_id=record.pk if link_field == "production_record" else None,
        exclude_stamping_id=record.pk if link_field == "stamping_record" else None,
    )

    if computed_start < last_covered:
        max_available = int((now - last_covered).total_seconds())
        raise ValidationError({
            "duration_seconds": (
                "La duración indicada se solapa con tiempo ya registrado en esta jornada. "
                f"Duración máxima disponible: {max_available} segundos."
            )
        })

    record.start_time = computed_start
    record.end_time = now
    record.save(update_fields=["start_time", "end_time"])

    if computed_start > last_covered:
        ModuleDowntime.objects.create(
            module=module,
            custom_reason=GAP_REASON_TEXT,
            start_time=last_covered,
            end_time=computed_start,
            created_by=record.created_by,
            updated_by=record.updated_by,
            **{link_field: record},
        )

    return record
