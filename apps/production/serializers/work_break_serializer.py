from apps.production.models.work_break import WorkBreak
from core.serializers.audit_serializer import AuditSerializer


class WorkBreakSerializer(AuditSerializer):
    class Meta:
        model = WorkBreak
        fields = "__all__"
