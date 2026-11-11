from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.views.audit_model_view import AuditModelViewSet
from core.views.recent_records_view import RecentRecordsMixin
from apps.production.services.op_record_batch_service import (
    perform_manual_duration_batch,
    simulate_manual_duration_batch,
)


class OpRecordViewSet(RecentRecordsMixin, AuditModelViewSet):
    """Common behavior of the production order record viewsets
    (ProductionRecordViewSet and StampingRecordViewSet).

    Children must set `queryset`, `serializer_class` and `module_type`
    ('production' or 'stamping', see ProductivityRepository).
    """

    module_type: str | None = None

    recent_records_user_filter = 'work_session_activity__work_session__user'
    recent_records_select_related = ('work_session_activity',)
    recent_records_dedup_field = 'op_rowid'

    def get_extra_available_seconds(self, request) -> float:
        """Hook: extra seconds added to the batch duration (see
        perform_manual_duration_batch). 0 unless the module needs it."""
        return 0.0

    @action(detail=False, methods=["post"], url_path="manual-duration-batch")
    def manual_duration_batch(self, request):
        """
        POST .../manual-duration-batch/

        See perform_manual_duration_batch (op_record_batch_service) for
        the payload and behavior details.
        """
        return perform_manual_duration_batch(
            self,
            request,
            tipo_modulo=self.module_type,
            extra_available_seconds=self.get_extra_available_seconds(request),
        )

    def get_batch_efficiency_lines(self, records) -> list:
        """Hook: one dict {sam, completed, total} per record, used by the
        manual-duration simulation (see _batch_efficiency). Children implement
        it because production and stamping resolve the SAM differently."""
        raise NotImplementedError

    @action(detail=False, methods=["post"], url_path="manual-duration-batch/simulate")
    def manual_duration_batch_simulate(self, request):
        """
        POST .../manual-duration-batch/simulate/

        Read-only: nothing is saved. Same payload as manual-duration-batch
        (duration_seconds may be null). Returns
        {min_duration_seconds, max_duration_seconds, efficiency}; see
        simulate_manual_duration_batch.
        """
        records = request.data.get('records')
        if not records or not isinstance(records, list):
            raise ValidationError({'records': 'Debe incluir al menos un registro.'})

        return Response(simulate_manual_duration_batch(
            request,
            tipo_modulo=self.module_type,
            lines=self.get_batch_efficiency_lines(records),
            extra_available_seconds=self.get_extra_available_seconds(request),
        ))
