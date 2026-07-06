from apps.production.models.work_shift import WorkShift
from core.serializers.audit_serializer import AuditSerializer
from core.serializers.module_serializer import ModuleSerializer


class WorkShiftSerializer(AuditSerializer):
    app_module_detail = ModuleSerializer(source="app_module", read_only=True)

    class Meta:
        model = WorkShift
        fields = "__all__"
