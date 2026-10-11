from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from apps.production.models.work_shift import WorkShift
from apps.production.models.module import Module
from apps.production.serializers.module_serializer import ModuleSerializer
from apps.production.serializers.work_shift_serializer import WorkShiftSerializer
from apps.production.models import WorkSession
from apps.production.serializers.production_record_serializer import ProductionRecordSerializer
from apps.production.serializers.work_break_record_serializer import WorkBreakRecordSerializer
from apps.production.services import work_session_setup_service
from core.serializers.audit_serializer import AuditSerializer


class WorkSessionSerializer(AuditSerializer):
    employee_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    apprentice_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
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
            raise ValidationError("Debe indicar module_id al enviar employee_ids.")

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
                "worked_minutes_per_hour": rel.worked_minutes_per_hour,
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

    def create(self, validated_data):
        return work_session_setup_service.create_session(validated_data)

    def update(self, instance, validated_data):
        return work_session_setup_service.update_session(instance, validated_data)
