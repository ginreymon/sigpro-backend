from rest_framework.decorators import action

from core.views.audit_model_view import AuditModelViewSet
from core.views.recent_records_view import RecentRecordsMixin
from apps.production.services.production_record_service import perform_manual_duration_batch


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

        See perform_manual_duration_batch (production_record_service) for
        the payload and behavior details.
        """
        return perform_manual_duration_batch(
            self,
            request,
            tipo_modulo=self.module_type,
            extra_available_seconds=self.get_extra_available_seconds(request),
        )
