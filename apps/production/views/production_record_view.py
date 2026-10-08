from rest_framework.decorators import action

from core.views.audit_model_view import AuditModelViewSet
from core.views.recent_records_view import RecentRecordsMixin
from apps.production.models import ProductionRecord
from apps.production.serializers import ProductionRecordSerializer
from apps.production.services.production_record_service import perform_manual_duration_batch


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

        See perform_manual_duration_batch (production_record_service) for
        the payload and behavior details — shared with its stamping
        counterpart (StampingRecordViewSet.manual_duration_batch).
        """
        return perform_manual_duration_batch(self, request, tipo_modulo='production')