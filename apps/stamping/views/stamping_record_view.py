from decimal import Decimal

from apps.common.views.op_record_view import OpRecordViewSet
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


class StampingRecordViewSet(OpRecordViewSet):
    queryset = StampingRecord.objects.all()
    serializer_class = StampingRecordSerializer
    module_type = 'stamping'

    def get_extra_available_seconds(self, request) -> float:
        """
        Stamping-specific adjustment of manual-duration-batch: the standard
        time of the additional_times of the whole batch (see
        _additional_times_extra_seconds) is added to duration_seconds both to
        validate against the shift's available time and for the span of the
        created ModuleDowntime — that time also occupied the shift.
        Production has no additional_times and is not affected.
        """
        records = request.data.get('records')
        return _additional_times_extra_seconds(records) if isinstance(records, list) else 0.0
