from rest_framework.decorators import action

from core.views.audit_model_view import AuditModelViewSet
from core.views.recent_records_view import RecentRecordsMixin
from apps.stamping.models.stamping_record import StampingRecord
from apps.stamping.serializers import StampingRecordSerializer


class StampingRecordViewSet(RecentRecordsMixin, AuditModelViewSet):
    queryset = StampingRecord.objects.all()
    serializer_class = StampingRecordSerializer

    recent_records_user_filter = 'work_session_activity__work_session__user'
    recent_records_select_related = ('work_session_activity',)
    recent_records_dedup_field = 'op_rowid'

    @action(detail=False, methods=["post"], url_path="manual-duration")
    def manual_duration(self, request, *args, **kwargs):
        """
        POST /stamping-records/manual-duration/

        Mantiene el endpoint por compatibilidad, pero se comporta igual que
        el create() normal (POST /stamping-records/).
        """
        return self.create(request, *args, **kwargs)
