from apps.production.models.work_break_record import WorkBreakRecord
from core.serializers.audit_serializer import AuditSerializer


class WorkBreakRecordSerializer(AuditSerializer):
    class Meta:
        model = WorkBreakRecord
        fields = "__all__"
