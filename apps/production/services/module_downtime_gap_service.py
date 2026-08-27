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

Además, antes de convertir el hueco en ModuleDowntime, se descuenta
cualquier tramo que ya esté justificado por otra fuente:

    - WorkBreakRecord de la MISMA actividad (pausa de empleado ya
      registrada — resta aparte vía break_seconds en la fórmula de meta).
      Si no se descontara, ese tramo se restaría dos veces: una como
      break_seconds y otra como module_break_seconds.
    - ModuleDowntime que ya exista en medio del hueco (real o autogenerado
      en una iteración anterior), por si quedara alguno fuera de orden.

Una pausa/paro sin cerrar (sin end_time/resumed_at) al momento del registro
se considera que cubre hasta "ahora" — igual criterio que ya usa
fn_paro_modulo_segundos para paros reales en curso.

Si la duración indicada por el usuario retrocede más allá del último punto
ya cubierto por producción/estampación/paro (antes de descontar pausas), se
rechaza con un ValidationError indicando la duración máxima disponible.
"""
from datetime import timedelta

from django.db.models import Max
from django.db.models.functions import Coalesce
from rest_framework.exceptions import ValidationError

from apps.production.models.module_downtime import ModuleDowntime

GAP_REASON_TEXT = "Tiempo no registrado"


def assert_manual_duration_allowed(module):
    """
    Valida que el módulo tenga habilitado el registro con duración manual
    (Module.allows_manual_duration_entry). Se llama ANTES de crear el
    ProductionRecord/StampingRecord — así, si el módulo no lo permite, no
    queda un registro huérfano a medio crear.
    """
    if not module.allows_manual_duration_entry:
        raise ValidationError({
            "work_session_activity": (
                f'El módulo "{module.name}" no tiene habilitado el registro con duración manual.'
            )
        })


def _last_covered_point(*, module, work_session, before):
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
    ).aggregate(m=Max("end_time"))["m"]

    last_stamping_end = StampingRecord.objects.filter(
        work_session_activity__work_session=work_session,
        work_session_activity__module=module,
        end_time__isnull=False,
        end_time__lte=before,
    ).aggregate(m=Max("end_time"))["m"]

    last_downtime_end = ModuleDowntime.objects.filter(
        module=module,
        start_time__gte=session_start,
        start_time__lt=before,
    ).annotate(
        effective_end=Coalesce("resumed_at", "end_time"),
    ).aggregate(m=Max("effective_end"))["m"]

    candidates = [d for d in (last_production_end, last_stamping_end, last_downtime_end) if d]
    return max(candidates) if candidates else session_start


def _justified_intervals(*, activity, module, gap_start, gap_end, now):
    """
    Intervalos dentro de [gap_start, gap_end] que ya están justificados por
    otra fuente y que por lo tanto NO deben duplicarse como ModuleDowntime:

        - WorkBreakRecord de la MISMA actividad (pausa de empleado).
        - ModuleDowntime que ya exista para el módulo (real o autogenerado
          en una iteración anterior) y caiga dentro del hueco.

    Un registro sin cerrar (resumed_at y end_time ambos NULL) se considera
    que cubre hasta `now`. Devuelve una lista de tramos ya fusionados
    (sin solapes entre sí), ordenados por inicio.
    """
    from apps.production.models.work_break_record import WorkBreakRecord

    raw = []

    breaks = WorkBreakRecord.objects.filter(
        work_session_activity=activity,
        start_time__lt=gap_end,
    ).annotate(effective_end=Coalesce("resumed_at", "end_time"))

    for br in breaks:
        end = br.effective_end or now
        start = max(br.start_time, gap_start)
        end = min(end, gap_end)
        if end > start:
            raw.append((start, end))

    downtimes = ModuleDowntime.objects.filter(
        module=module,
        start_time__lt=gap_end,
    ).annotate(effective_end=Coalesce("resumed_at", "end_time"))

    for md in downtimes:
        end = md.effective_end or now
        start = max(md.start_time, gap_start)
        end = min(end, gap_end)
        if end > start:
            raw.append((start, end))

    raw.sort(key=lambda pair: pair[0])

    merged = []
    for start, end in raw:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    return merged


def _uncovered_segments(*, gap_start, gap_end, justified):
    """Complemento de `justified` dentro de [gap_start, gap_end]."""
    segments = []
    cursor = gap_start

    for start, end in justified:
        if start > cursor:
            segments.append((cursor, start))
        cursor = max(cursor, end)

    if cursor < gap_end:
        segments.append((cursor, gap_end))

    return segments


def apply_manual_duration(*, record, work_session, duration_seconds, link_field):
    """
    Ajusta start_time/end_time de `record` (ProductionRecord o
    StampingRecord recién creado — llega con start_time = end_time = now,
    puesto por auto_now_add) según la duración indicada manualmente, y crea
    el/los ModuleDowntime que cubren el hueco previo (si existe), enlazados
    al registro por FK exacto — no por solape de fechas.

    Antes de crear cada ModuleDowntime, descuenta del hueco cualquier tramo
    ya justificado por un WorkBreakRecord de la misma actividad o por un
    ModuleDowntime existente en medio del hueco — así nunca se resta dos
    veces el mismo tiempo real (una vía break_seconds y otra vía
    module_break_seconds), y puede resultar en 0, 1 o varios ModuleDowntime
    según cuántos tramos sin justificar queden.

    Parámetros:
        record            Instancia ya guardada (ProductionRecord o
                           StampingRecord).
        work_session       Jornada activa (record.work_session_activity.work_session).
        duration_seconds  Duración en segundos indicada por el usuario.
        link_field        "production_record" o "stamping_record" — el FK
                           de ModuleDowntime que corresponde a este tipo de
                           registro.

    Lanza ValidationError si la duración se solapa con tiempo ya cubierto
    por producción/estampación/paro (antes de descontar pausas).
    """
    activity = record.work_session_activity
    module = activity.module
    now = record.start_time

    computed_start = now - timedelta(seconds=duration_seconds)

    last_covered = _last_covered_point(module=module, work_session=work_session, before=now)

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
        justified = _justified_intervals(
            activity=activity,
            module=module,
            gap_start=last_covered,
            gap_end=computed_start,
            now=now,
        )

        for seg_start, seg_end in _uncovered_segments(
            gap_start=last_covered, gap_end=computed_start, justified=justified
        ):
            ModuleDowntime.objects.create(
                module=module,
                custom_reason=GAP_REASON_TEXT,
                start_time=seg_start,
                end_time=seg_end,
                created_by=record.created_by,
                updated_by=record.updated_by,
                **{link_field: record},
            )

    return record
