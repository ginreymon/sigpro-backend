from rest_framework import serializers
from apps.production.models.module import Module
from apps.production.models.work_center_local import WorkCenterLocal
from .work_center_local_serializer import WorkCenterLocalSerializer


class ModuleSerializer(serializers.ModelSerializer):
    work_center = WorkCenterLocalSerializer(read_only=True)

    work_center_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkCenterLocal.objects.all(),
        source="work_center",
        write_only=True
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

