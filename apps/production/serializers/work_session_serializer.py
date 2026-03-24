from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from apps.production.models.work_shift import WorkShift
from apps.production.models.module import Module
from apps.production.serializers.module_serializer import ModuleSerializer
from apps.production.serializers.work_shift_serializer import WorkShiftSerializer
from apps.production.models import WorkSession, ModuleAssignee, EmployeeLocal
from apps.production.serializers.work_session_activity_serializer import WorkSessionActivitySerializer
from django.db import transaction
from core.serializers.audit_serializer import AuditSerializer


class WorkSessionSerializer(AuditSerializer):
    employee_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True)
    current_module = serializers.SerializerMethodField()
    work_shift = WorkShiftSerializer(read_only=True)
    modules = serializers.SerializerMethodField()

    module_id = serializers.PrimaryKeyRelatedField(
        queryset=Module.objects.all(), source="module", write_only=True, required=False, allow_null=True,
    )

    work_shift_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkShift.objects.all(), source="work_shift", write_only=True
    )

    class Meta:
        model = WorkSession
        fields = "__all__"
        read_only_fields = ("user", "total_time", "is_closed")


    def get_current_module(self, obj):
        activity = getattr(obj, "_prefetched_active_activity", None)

        if activity:
            activity = activity[0] if isinstance(activity, list) else activity
            return ModuleSerializer(activity.module).data

        activity = obj.get_active_activity()

        return ModuleSerializer(activity.module).data if activity else None
    

    def get_modules(self, obj):
        activities = obj.work_session_activities.all().order_by("started_at")

        active_activities = getattr(obj, "_prefetched_active_activity", None)
       
        if active_activities:
            active_activity = active_activities[0] if isinstance(active_activities, list) else active_activities
            activities = activities.exclude(id=active_activity.id)

        return WorkSessionActivitySerializer(activities, many=True).data


    def _handle_employees(self, instance, employee_ids):
        # Update snapshot
        instance.employees_snapshot = [
            {
                "id": emp.id,
                "first_name": emp.first_name,
                "last_name1": emp.last_name1,
                "last_name2": emp.last_name2,
            }
            for emp in EmployeeLocal.objects.filter(id__in=employee_ids)
        ]
        instance.save()

        activity = instance.get_active_activity()

        if not activity:
            raise ValidationError("No active activity found")

        module = activity.module
        current_assignees = ModuleAssignee.objects.filter(module=module)
        current_employee_ids = set(
            current_assignees.values_list("employee_id", flat=True)
        )

        new_employee_ids = set(employee_ids)

        to_add = new_employee_ids - current_employee_ids
        to_remove = current_employee_ids - new_employee_ids

        if to_remove:
            ModuleAssignee.objects.filter(
                module=module,
                employee_id__in=to_remove
            ).delete()

        assignees_to_create = [
            ModuleAssignee(
                module=module,
                employee_id=emp_id,
                created_by=getattr(instance, "updated_by", None) or instance.created_by,
            )
            for emp_id in to_add
        ]

        ModuleAssignee.objects.bulk_create(assignees_to_create)


    @transaction.atomic
    def create(self, validated_data):
        employee_ids = validated_data.pop("employee_ids", [])
        module = validated_data.pop("module_id", None)

        if not module:
            raise serializers.ValidationError({"module_id": "This field is required."})

        work_session = super().create(validated_data)
        work_session.start_activity(module)

        if employee_ids:
            self._handle_employees(work_session, employee_ids)

        return work_session
    
    
    @transaction.atomic
    def update(self, instance, validated_data):
        employee_ids = validated_data.pop("employee_ids", None)
        module = validated_data.pop("module_id", None)

        instance = super().update(instance, validated_data)

        if module is not None:
            instance.start_activity(module)

        if employee_ids is not None:
            self._handle_employees(instance, employee_ids)

        return instance