from decimal import Decimal, InvalidOperation

from rest_framework.decorators import action
from rest_framework.response import Response

from apps.production.services.op_record_batch_service import (
    assert_single_record_within_cap,
    simulate_single_record,
)
from apps.production.views.op_record_view import OpRecordViewSet
from apps.stamping.models.additional_stamping_time import AdditionalStampingTime
from apps.stamping.models.stamping_record import StampingRecord
from apps.stamping.models.stamping_reference_sam import StampingReferenceSam
from apps.stamping.serializers import StampingRecordSerializer
from core import option_keys as opt


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
        .values_list('id', 'standard_time_minutes')
    )
    total_minutes = sum(
        (Decimal(str(standard_times.get(item_id) or 0)) * count for item_id, count in counts_by_id.items()),
        Decimal('0'),
    )
    return float(total_minutes * 60)


class StampingRecordViewSet(OpRecordViewSet):
    write_options = (opt.STAMP_SHIFT_CYCLES, *opt.SESSION_EDITORS_ADMIN)

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

    def _single_record_check_args(self, request) -> dict:
        """Arguments of the efficiency check of one regular record (request.data is the record)."""
        record = request.data
        return {
            'request': request,
            'tipo_modulo': self.module_type,
            'lines': self.get_batch_efficiency_lines([record]),
            'extra_seconds': _additional_times_extra_seconds([record]),
        }

    @action(detail=False, methods=["post"], url_path="simulate")
    def simulate(self, request):
        """POST .../stamping-records/simulate/ — read-only efficiency check of a
        regular record (same payload as create()); see simulate_single_record."""
        return Response(simulate_single_record(**self._single_record_check_args(request)))

    def create(self, request, *args, **kwargs):
        # Regular (non-manual) flow only: the manual batch saves through
        # perform_create and has its own cap check (perform_manual_duration_batch).
        assert_single_record_within_cap(**self._single_record_check_args(request))
        return super().create(request, *args, **kwargs)

    def get_batch_efficiency_lines(self, records) -> list:
        """SAM per record: stamping_reference_sam (id) -> StampingReferenceSam.sam.
        Stamping has no scrap/rejected: total == completed."""
        ids = {r.get('stamping_reference_sam') for r in records if isinstance(r, dict)}
        sam_by_id = dict(
            StampingReferenceSam.objects.filter(id__in=[x for x in ids if x is not None])
            .values_list('id', 'sam')
        )
        lines = []
        for r in records:
            try:
                completed = float(Decimal(str(r.get('completed_quantity') or 0)))
            except InvalidOperation:
                completed = 0.0
            lines.append({
                'sam': float(sam_by_id.get(r.get('stamping_reference_sam')) or 0),
                'completed': completed,
                'total': completed,
            })
        return lines
