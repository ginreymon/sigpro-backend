from rest_framework.decorators import action

from core.views.audit_model_view import AuditModelViewSet
from core.views.recent_records_view import RecentRecordsMixin
from apps.production.services.production_record_service import perform_manual_duration_batch
from apps.stamping.models.stamping_record import StampingRecord
from apps.stamping.serializers import StampingRecordSerializer


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
        perform_manual_duration_batch) para registros de estampación.
        """
        return perform_manual_duration_batch(self, request, tipo_modulo='stamping')
