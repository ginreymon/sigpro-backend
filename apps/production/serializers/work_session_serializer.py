from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from apps.production.models.work_shift import WorkShift
from apps.production.models.module import Module
from apps.production.serializers.module_serializer import ModuleSerializer
from apps.production.serializers.work_shift_serializer import WorkShiftSerializer
from apps.production.models import WorkSession, ModuleAssignee, EmployeeLocal
from apps.production.serializers.production_record_serializer import ProductionRecordSerializer
from apps.production.models.work_session_activity_employee import WorkSessionActivityEmployee
from django.db import transaction
from core.serializers.audit_serializer import AuditSerializer


class WorkSessionSerializer(AuditSerializer):
    employee_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    apprentice_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False, default=list)
    current_module = serializers.SerializerMethodField()
    work_shift = WorkShiftSerializer(read_only=True)
    modules = serializers.SerializerMethodField()
    employees_snapshot = serializers.SerializerMethodField()
    active_activity = serializers.SerializerMethodField()

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

        if employee_ids and not module and not self.instance:
            raise ValidationError("module_id is required when sending employee_ids")

        return attrs

    def _get_active_activity(self, obj):
        if not hasattr(obj, '_cached_active_activity'):
            obj._cached_active_activity = max(
                (a for a in obj.work_session_activities.all() if a.is_active and a.ended_at is None),
                key=lambda a: (a.started_at, a.id),
                default=None,
            )
        return obj._cached_active_activity

    def get_current_module(self, obj):
        activity = self._get_active_activity(obj)
        return ModuleSerializer(activity.module).data if activity else None

    def get_modules(self, obj):
        seen = {}
        for activity in obj.work_session_activities.all():
            m = activity.module
            if m.id not in seen:
                seen[m.id] = {"id": m.id, "name": m.name, "number": m.number}
        return list(seen.values())

    def get_employees_snapshot(self, obj):
        activity = self._get_active_activity(obj)

        if not activity:
            return []

        return [
            {
                "id": rel.employee.id,
                "first_name": rel.employee.first_name,
                "last_name1": rel.employee.last_name1,
                "last_name2": rel.employee.last_name2,
                "is_apprentice": rel.is_apprentice,
            }
            for rel in activity.employee_snapshots.all()
        ]

    def get_active_activity(self, obj):
        activity = self._get_active_activity(obj)

        if not activity:
            return None

        last_open_record = activity.last_open_production_record
        last_record = activity.last_production_record
        active_break = activity.active_break

        from apps.production.serializers.work_break_record_serializer import WorkBreakRecordSerializer

        return {
            "id": activity.id,
            "started_at": activity.started_at,
            "ended_at": activity.ended_at,
            "is_active": activity.is_active,
            "is_paused": activity.is_paused,
            "total_pause_time_seconds": activity.total_pause_time.total_seconds(),
            "active_break": (
                WorkBreakRecordSerializer(active_break).data if active_break else None
            ),
            "last_open_production_record": (
                ProductionRecordSerializer(last_open_record, context={**self.context, "activity": activity}).data
                if last_open_record else None
            ),
            "last_production_record": (
                ProductionRecordSerializer(last_record, context={**self.context, "activity": activity}).data
                if last_record else None
            ),
        }

    def _handle_employees(self, instance, employee_ids, activity=None, apprentice_ids=None):
        if not activity:
            activity = instance.get_active_activity()

        if not activity:
            raise ValidationError("No active activity found")

        employees = EmployeeLocal.objects.filter(id__in=employee_ids)
        apprentice_set = set(apprentice_ids or [])

        WorkSessionActivityEmployee.objects.filter(work_session_activity=activity).delete()

        WorkSessionActivityEmployee.objects.bulk_create(
            [
                WorkSessionActivityEmployee(
                    work_session_activity=activity,
                    employee=emp,
                    is_apprentice=emp.id in apprentice_set,
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
        apprentice_ids = validated_data.pop("apprentice_ids", [])
        module = validated_data.pop("module_id", None)

        work_session = super().create(validated_data)

        activity = None

        if module:
            activity = work_session.start_activity(module)

        if employee_ids:
            if not activity:
                raise ValidationError("Cannot assign employees without a module")

            self._handle_employees(work_session, employee_ids, activity, apprentice_ids)

        return work_session

    @transaction.atomic
    def update(self, instance, validated_data):
        employee_ids = validated_data.pop("employee_ids", None)
        apprentice_ids = validated_data.pop("apprentice_ids", None)
        module = validated_data.pop("module_id", None)

        # Capture current state before any changes
        current_activity = instance.get_active_activity()
        current_module = current_activity.module if current_activity else None
        current_employee_ids = set(
            current_activity.employee_snapshots.values_list("employee_id", flat=True)
        ) if current_activity else set()
        current_apprentice_ids = set(
            current_activity.employee_snapshots.filter(is_apprentice=True).values_list("employee_id", flat=True)
        ) if current_activity else set()

        new_work_shift = validated_data.get("work_shift")

        module_changed = module is not None and module != current_module
        work_shift_changed = new_work_shift is not None and new_work_shift != instance.work_shift
        employees_changed = employee_ids is not None and set(employee_ids) != current_employee_ids
        apprentice_changed = apprentice_ids is not None and set(apprentice_ids) != current_apprentice_ids

        any_field_changed = module_changed or work_shift_changed or employees_changed or apprentice_changed

        instance = super().update(instance, validated_data)

        if any_field_changed:
            target_module = module or current_module
            if not target_module:
                return instance

            activity = instance.start_activity(target_module)
            effective_ids = list(employee_ids) if employee_ids is not None else list(current_employee_ids)
            effective_apprentice_ids = list(apprentice_ids) if apprentice_ids is not None else list(current_apprentice_ids)
            self._handle_employees(instance, effective_ids, activity, effective_apprentice_ids)

        return instance
