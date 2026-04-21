from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from apps.production.models.work_shift import WorkShift
from apps.production.models.module import Module
from apps.production.serializers.module_serializer import ModuleSerializer
from apps.production.serializers.work_shift_serializer import WorkShiftSerializer
from apps.production.models import WorkSession, ModuleAssignee, EmployeeLocal
from apps.production.serializers.work_session_activity_serializer import WorkSessionActivitySerializer
from apps.production.models.work_session_activity_employee import WorkSessionActivityEmployee
from django.db import transaction
from core.serializers.audit_serializer import AuditSerializer


class WorkSessionSerializer(AuditSerializer):
    employee_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    current_module = serializers.SerializerMethodField()
    work_shift = WorkShiftSerializer(read_only=True)
    modules = serializers.SerializerMethodField()
    employees_snapshot = serializers.SerializerMethodField()

    module_id = serializers.PrimaryKeyRelatedField(
        queryset=Module.objects.all(), write_only=True, required=False, allow_null=True,
    )

    work_shift_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkShift.objects.all(), source="work_shift", write_only=True
    )

    class Meta:
        model = WorkSession
        fields = "__all__"
        read_only_fields = ("user", "total_time", "is_closed")

    def validate(self, attrs):
        employee_ids = attrs.get("employee_ids")
        module = attrs.get("module_id")

        if employee_ids and not module:
            raise ValidationError("module_id is required when sending employee_ids")

        return attrs

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

    def get_employees_snapshot(self, obj):
        activity = obj.get_active_activity()

        if not activity:
            return []

        return [
            {
                "id": rel.employee.id,
                "first_name": rel.employee.first_name,
                "last_name1": rel.employee.last_name1,
                "last_name2": rel.employee.last_name2,
            }
            for rel in activity.employee_snapshots.select_related("employee").all()
        ]

    def _handle_employees(self, instance, employee_ids, activity=None):   
        if not activity:
            activity = instance.get_active_activity()

        if not activity:
            raise ValidationError("No active activity found")

        employees = EmployeeLocal.objects.filter(id__in=employee_ids)

        WorkSessionActivityEmployee.objects.filter(
            work_session_activity=activity
        ).delete()

        WorkSessionActivityEmployee.objects.bulk_create(
            [
                WorkSessionActivityEmployee(
                    work_session_activity=activity,
                    employee=emp,
                    created_by=getattr(instance, "updated_by", None)
                    or instance.created_by,
                )
                for emp in employees
            ]
        )

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

        work_session = super().create(validated_data)

        activity = None

        if module:
            activity = work_session.start_activity(module)

        if employee_ids:
            if not activity:
                raise ValidationError("Cannot assign employees without a module")

            self._handle_employees(work_session, employee_ids, activity)

        return work_session

    @transaction.atomic
    def update(self, instance, validated_data):
        employee_ids = validated_data.pop("employee_ids", None)
        module = validated_data.pop("module_id", None)

        instance = super().update(instance, validated_data)

        activity = None

        if module is not None:
            activity = instance.start_activity(module)

        if employee_ids is not None:
            if not activity:
                activity = instance.get_active_activity()

            if not activity:
                raise ValidationError(
                    "Cannot assign employees without an active module"
                )

            self._handle_employees(instance, employee_ids, activity)

        return instance
