from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from apps.production.models.module_assignee import ModuleAssignee
from core.serializers.audit_serializer import AuditSerializer
from .module_serializer import ModuleSerializer


class ModuleAssigneeSerializer(AuditSerializer):
    module_detail = ModuleSerializer(source="module", read_only=True)
    module_name = serializers.CharField(source="module.name", read_only=True)
    employee_full_name = serializers.SerializerMethodField()
    employee_id_number = serializers.CharField(source="employee.id_number", read_only=True)

    class Meta:
        model = ModuleAssignee
        fields = "__all__"
        validators = [
            UniqueTogetherValidator(
                queryset=ModuleAssignee.objects.all(),
                fields=("module", "employee"),
                message="Este empleado ya está asignado a este módulo.",
            )
        ]

    def get_employee_full_name(self, obj):
        e = obj.employee
        return " ".join(p for p in (e.first_name, e.last_name1, e.last_name2) if p)
