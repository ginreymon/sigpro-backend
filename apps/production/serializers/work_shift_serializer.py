from apps.production.models.work_shift import WorkShift
from core.serializers.audit_serializer import AuditSerializer


class WorkShiftSerializer(AuditSerializer):
    class Meta:
        model = WorkShift
        fields = "__all__"
