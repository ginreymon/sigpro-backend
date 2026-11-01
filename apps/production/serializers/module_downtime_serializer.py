from apps.production.models.module_downtime import ModuleDowntime
from core.serializers.audit_serializer import AuditSerializer


class ModuleDowntimeSerializer(AuditSerializer):
    class Meta:
        model = ModuleDowntime
        fields = "__all__"
