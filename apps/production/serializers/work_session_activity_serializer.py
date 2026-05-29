from rest_framework import serializers
from django.utils import timezone
from django.db.models import F
from apps.production.models import WorkSessionActivity, WorkSession
from apps.production.models.module import Module
from apps.production.serializers.module_serializer import ModuleSerializer
from apps.production.serializers.production_record_serializer import ProductionRecordSerializer
from apps.production.serializers.work_break_record_serializer import WorkBreakRecordSerializer
from core.serializers.audit_serializer import AuditSerializer


class WorkSessionActivitySerializer(AuditSerializer):
    module = ModuleSerializer(read_only=True)
    module_id = serializers.PrimaryKeyRelatedField(
        queryset=Module.objects.all(), write_only=True, source="module"
    )
    work_session = serializers.PrimaryKeyRelatedField(
        queryset=WorkSession.objects.all()
    )

    duration_seconds = serializers.SerializerMethodField()
    total_pause_time_seconds = serializers.SerializerMethodField()
    active_time_seconds = serializers.SerializerMethodField()
    is_paused = serializers.BooleanField(read_only=True)
    active_break = serializers.SerializerMethodField()
    work_break_records = WorkBreakRecordSerializer(many=True, read_only=True)
    last_open_production_record = serializers.SerializerMethodField()
    last_production_record = serializers.SerializerMethodField()

    class Meta:
        model = WorkSessionActivity
        fields = [
            "id",
            "work_session",
            "module",
            "module_id",
            "started_at",
            "ended_at",
            "is_active",
            "is_paused",
            "active_break",
            "duration_seconds",
            "total_pause_time_seconds",
            "active_time_seconds",
            "work_break_records",
            "last_open_production_record",
            "last_production_record",
            "created_by",
            "created_by_username",
            "updated_by",
            "updated_by_username",
        ]

    def get_duration_seconds(self, obj):
        end = obj.ended_at or timezone.now()
        return int((end - obj.started_at).total_seconds())

    def get_total_pause_time_seconds(self, obj):
        return int(obj.total_pause_time.total_seconds())

    def get_active_time_seconds(self, obj):
        end = obj.ended_at or timezone.now()
        total = int((end - obj.started_at).total_seconds())
        pause = int(obj.total_pause_time.total_seconds())
        return max(total - pause, 0)

    def get_active_break(self, obj):
        br = obj.active_break
        if not br:
            return None
        return WorkBreakRecordSerializer(br).data

    def get_last_open_production_record(self, obj):
        record = obj.last_open_production_record
        if not record:
            return None
        return ProductionRecordSerializer(record).data

    def get_last_production_record(self, obj):
        record = obj.last_production_record
        if not record:
            return None
        return ProductionRecordSerializer(record).data

    def to_representation(self, instance):
        now = timezone.now()
        closed = instance.work_break_records.filter(
            work_break__isnull=False,
            end_time__isnull=False,
            end_time__lte=now,
            resumed_at__isnull=True,
        ).update(resumed_at=F('end_time'))
        if closed > 0:
            instance.refresh_from_db()
        return super().to_representation(instance)

    def create(self, validated_data):
        work_session = validated_data["work_session"]
        module = validated_data["module"]
        created_by = validated_data.get("created_by")
        return work_session.start_activity(module=module, created_by=created_by)
