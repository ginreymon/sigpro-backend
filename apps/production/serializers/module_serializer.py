from rest_framework import serializers
from apps.production.models.module import Module
from apps.production.models.work_center_local import WorkCenterLocal
from apps.production.models.production_area import ProductionArea
from .work_center_local_serializer import WorkCenterLocalSerializer
from .production_area_serializer import ProductionAreaSerializer
from core.serializers.audit_serializer import AuditSerializer


class ModuleSerializer(AuditSerializer):
    work_center = WorkCenterLocalSerializer(read_only=True)

    work_center_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkCenterLocal.objects.all(), source="work_center", write_only=True
    )

    location = ProductionAreaSerializer(read_only=True)

    location_id = serializers.PrimaryKeyRelatedField(
        queryset=ProductionArea.objects.all(),
        source="location",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Module
        fields = "__all__"

    employees = serializers.SerializerMethodField()

    def get_employees(self, obj):
        assignees = obj.moduleassignee_set.select_related("employee")
        return [
            {
                "id": a.employee.id,
                "first_name": a.employee.first_name,
                "last_name1": a.employee.last_name1,
                "last_name2": a.employee.last_name2,
            }
            for a in assignees
        ]
