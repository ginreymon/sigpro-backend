from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.views.audit_model_view import AuditModelViewSet
from core.views.recent_records_view import RecentRecordsMixin
from apps.stamping.models.stamping_record import StampingRecord
from apps.stamping.serializers import StampingRecordSerializer
from apps.stamping.serializers.stamping_record_manual_serializer import (
    StampingRecordManualDurationSerializer,
)


class StampingRecordViewSet(RecentRecordsMixin, AuditModelViewSet):
    queryset = StampingRecord.objects.all()
    serializer_class = StampingRecordSerializer

    recent_records_user_filter = 'work_session_activity__work_session__user'
    recent_records_select_related = ('work_session_activity',)
    recent_records_dedup_field = 'op_rowid'

    @action(detail=False, methods=["post"], url_path="registro-manual")
    def registro_manual(self, request, *args, **kwargs):
        """
        POST /stamping-records/registro-manual/

        Igual que el create() normal, pero recibe `duration_seconds` y
        calcula start_time/end_time a partir de esa duración, generando el
        ModuleDowntime del hueco previo cuando corresponde. No afecta el
        endpoint de creación existente.
        """
        serializer = StampingRecordManualDurationSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
