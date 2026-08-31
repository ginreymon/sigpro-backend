from django.db import transaction
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.utils.date_utils import to_utc_naive
from core.views.audit_model_view import AuditModelViewSet
from core.views.recent_records_view import RecentRecordsMixin
from apps.production.models import ProductionRecord, WorkSession, WorkShiftSnapshot
from apps.production.repositories.productivity_repository import ProductivityRepository
from apps.production.serializers import ProductionRecordSerializer
from apps.production.services.production_record_service import (
    create_manual_duration_batch_downtime,
)
from apps.production.services.work_session_service import shift_start_utc


def _active_work_session_and_activity(request):
    """
    Resuelve la jornada (sesión) abierta del usuario y su actividad activa
    actual (o (None, None) si no hay ninguna). Es la fuente de verdad del
    servidor — nunca hay que confiar en un work_session_activity que venga
    ya armado desde el frontend, porque puede haberse cerrado/rotado desde
    que se armó ese payload.
    """
    work_session = WorkSession.objects.filter(user=request.user, is_closed=False).first()
    if not work_session:
        return None, None

    activity = work_session.get_active_activity()
    return work_session, activity


def _manual_duration_indicators(work_session, activity):
    """
    Indicadores de tiempo del turno para `activity`, usados para validar
    duration_seconds contra el turno. None si no hay jornada/actividad activa.
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
        tipo_modulo='production',
    )


class ProductionRecordViewSet(RecentRecordsMixin, AuditModelViewSet):
    queryset = ProductionRecord.objects.all()
    serializer_class = ProductionRecordSerializer

    recent_records_user_filter = 'work_session_activity__work_session__user'
    recent_records_select_related = ('work_session_activity',)
    recent_records_dedup_field = 'op_rowid'

    @action(detail=False, methods=["post"], url_path="manual-duration-batch")
    def manual_duration_batch(self, request):
        """
        POST /production-records/manual-duration-batch/

        Payload: { "records": [<mismo shape que POST /production-records/>, ...],
                    "duration_seconds": <segundos del lote completo, uno o más registros> }

        duration_seconds cubre el lote entero (no cada registro individual):
        se valida una sola vez contra el turno y luego se guarda cada registro
        exactamente como POST /production-records/ (mismo create() del
        serializer, todo-o-nada dentro de una transacción). Además crea un
        único ModuleDowntime que cubre esa duración, enlazado al primer
        registro del lote (ver create_manual_duration_batch_downtime). La
        respuesta es la lista de todos los registros guardados (mismo
        serializer.data que un create() normal), cada uno con el
        duration_seconds del lote.
        """
        records = request.data.get('records')
        if not records or not isinstance(records, list):
            raise ValidationError({'records': 'Debe incluir al menos un registro.'})

        duration_seconds = request.data.get('duration_seconds')
        if duration_seconds is None:
            raise ValidationError({'duration_seconds': 'Este campo es requerido.'})

        work_session, activity = _active_work_session_and_activity(request)
        indicators = _manual_duration_indicators(work_session, activity)
        if not indicators:
            raise ValidationError({'duration_seconds': 'No hay una jornada (sesión) activa.'})

        with transaction.atomic():
            created = []
            # El work_session_activity que trae cada registro del lote se
            # capturó en el frontend al encolarse (ManualProductionRecordsStore),
            # que puede llevar rato abierto — para cuando se confirma el lote
            # esa actividad puede ya estar cerrada (rotación de actividad,
            # fin de turno, etc). El servidor es la fuente de verdad: todos
            # los registros se fuerzan a la actividad realmente activa ahora,
            # y si ProductionRecordSerializer.create() la rota a mitad de
            # lote (cambio de SKU, ver _open_new_activity), los siguientes
            # registros siguen esa rotación.
            current_activity_id = activity.id if activity else None
            first_instance = None
            record_ids = []
            for record in records:
                if current_activity_id is not None:
                    record = {**record, 'work_session_activity': current_activity_id}

                serializer = self.get_serializer(data=record)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
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