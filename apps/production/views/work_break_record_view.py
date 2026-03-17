from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import WorkBreakRecord
from apps.production.serializers import WorkBreakRecordSerializer


class WorkBreakRecordViewSet(AuditModelViewSet):
    queryset = WorkBreakRecord.objects.all()
    serializer_class = WorkBreakRecordSerializer
