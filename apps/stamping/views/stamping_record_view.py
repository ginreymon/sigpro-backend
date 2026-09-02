from decimal import Decimal

from rest_framework.decorators import action

from core.views.audit_model_view import AuditModelViewSet
from core.views.recent_records_view import RecentRecordsMixin
from apps.production.services.production_record_service import perform_manual_duration_batch
from apps.stamping.models.additional_stamping_time import AdditionalStampingTime
from apps.stamping.models.stamping_record import StampingRecord
from apps.stamping.serializers import StampingRecordSerializer


def _additional_times_extra_seconds(records) -> float:
    """
    Estampación valida el tiempo estándar de los additional_times de todo
    el lote contra el disponible del turno además de duration_seconds —
    producción no tiene additional_times y no participa en esta cuenta.

    Cada registro trae additional_times: [{id, count}, ...] (mismo shape
    que valida StampingRecordSerializer). Por cada item se multiplica
    standard_time (AdditionalStampingTime, minutos por unidad — mismo
    criterio que app-additional-stamping-time-card) por count, se suma
    todo el lote y se convierte a segundos.
    """
    counts_by_id: dict = {}
    for record in records:
        for item in (record.get('additional_times') or []):
            item_id = item.get('id') if isinstance(item, dict) else None
            if item_id is None:
                continue
            count = Decimal(str(item.get('count') or 0))
            counts_by_id[item_id] = counts_by_id.get(item_id, Decimal('0')) + count

    if not counts_by_id:
        return 0.0

    standard_times = dict(
        AdditionalStampingTime.objects.filter(id__in=counts_by_id.keys())
        .values_list('id', 'standard_time')
    )
    total_minutes = sum(
        (Decimal(str(standard_times.get(item_id) or 0)) * count for item_id, count in counts_by_id.items()),
        Decimal('0'),
    )
    return float(total_minutes * 60)


class StampingRecordViewSet(RecentRecordsMixin, AuditModelViewSet):
    queryset = StampingRecord.objects.all()
    serializer_class = StampingRecordSerializer

    recent_records_user_filter = 'work_session_activity__work_session__user'
    recent_records_select_related = ('work_session_activity',)
    recent_records_dedup_field = 'op_rowid'

    @action(detail=False, methods=["post"], url_path="manual-duration-batch")
    def manual_duration_batch(self, request):
        """
        POST /stamping-records/manual-duration-batch/

        Homólogo a production-records/manual-duration-batch/ (ver
        perform_manual_duration_batch), con una validación adicional
        propia de estampación: el tiempo estándar de los additional_times
        de todo el lote se suma a duration_seconds antes de comparar
        contra el tiempo disponible del turno (ver
        _additional_times_extra_seconds) — producción no la aplica.
        """
        records = request.data.get('records')
        extra_seconds = _additional_times_extra_seconds(records) if isinstance(records, list) else 0.0
        return perform_manual_duration_batch(
            self, request, tipo_modulo='stamping', extra_available_seconds=extra_seconds,
        )
