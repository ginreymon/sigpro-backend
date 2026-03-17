from rest_framework import serializers
from apps.production.models import WorkSession, ModuleAssignee, EmployeeLocal
from django.db import transaction


class WorkSessionSerializer(serializers.ModelSerializer):
    employee_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True)

    class Meta:
        model = WorkSession
        fields = "__all__"
        read_only_fields = ("user", "total_time", "is_closed")

    @transaction.atomic
    def create(self, validated_data):
        employee_ids = validated_data.pop("employee_ids", [])

        validated_data["employees_snapshot"] = [
            {
                "id": emp.id,
                "first_name": emp.first_name,
                "last_name1": emp.last_name1,
                "last_name2": emp.last_name2,             
            }
            for emp in EmployeeLocal.objects.filter(id__in=employee_ids)
        ]

        work_session = WorkSession.objects.create(**validated_data)

        module = work_session.module

        current_assignees = ModuleAssignee.objects.filter(module=module)
        current_employee_ids = set(
            current_assignees.values_list("employee_id", flat=True)
        )

        new_employee_ids = set(employee_ids)

        to_add = new_employee_ids - current_employee_ids

        to_remove = current_employee_ids - new_employee_ids

        if to_remove:
            ModuleAssignee.objects.filter(
                module=module, employee_id__in=to_remove
            ).delete()

        assignees_to_create = [
            ModuleAssignee(
                module=module, employee_id=emp_id, created_by=work_session.user
            )
            for emp_id in to_add
        ]

        ModuleAssignee.objects.bulk_create(assignees_to_create)

        return work_session
