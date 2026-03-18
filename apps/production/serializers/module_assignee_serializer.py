from apps.production.models.module_assignee import ModuleAssignee
from core.serializers.audit_serializer import AuditSerializer


class ModuleAssigneeSerializer(AuditSerializer):
    class Meta:
        model = ModuleAssignee
        fields = "__all__"
