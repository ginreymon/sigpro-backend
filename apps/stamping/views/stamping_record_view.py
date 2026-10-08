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
    Stamping validates the standard time of the additional_times of the whole
    batch against the shift's available time in addition to duration_seconds —
    production has no additional_times and does not take part in this sum.

    Each record carries additional_times: [{id, count}, ...] (same shape
    that StampingRecordSerializer validates). For each item, standard_time
    (AdditionalStampingTime, minutes per unit — same criterion as
    app-additional-stamping-time-card) is multiplied by count, the whole
    batch is summed and the result is converted to seconds.
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

        Counterpart of production-records/manual-duration-batch/ (see
        perform_manual_duration_batch), with an extra adjustment specific to
        stamping: the standard time of the additional_times of the whole
        batch (see _additional_times_extra_seconds) is added to
        duration_seconds both to validate against the shift's available
        time and for the span of the created ModuleDowntime — that time
        also occupied the shift. Production has no additional_times
        and is not affected.
        """
        records = request.data.get('records')
        extra_seconds = _additional_times_extra_seconds(records) if isinstance(records, list) else 0.0
        return perform_manual_duration_batch(
            self, request, tipo_modulo='stamping', extra_available_seconds=extra_seconds,
        )
