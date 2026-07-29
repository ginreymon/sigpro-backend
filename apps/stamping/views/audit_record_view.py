from core.views.audit_model_view import AuditModelViewSet
from apps.stamping.models.audit_record import AuditRecord
from apps.stamping.serializers import AuditRecordSerializer


class AuditRecordViewSet(AuditModelViewSet):
    queryset = AuditRecord.objects.all()
    serializer_class = AuditRecordSerializer
