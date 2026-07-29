from core.serializers.audit_serializer import AuditSerializer
from apps.stamping.models.audit_record import AuditRecord


class AuditRecordSerializer(AuditSerializer):

    class Meta:
        model = AuditRecord
        fields = "__all__"
