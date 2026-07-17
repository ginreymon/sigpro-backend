from rest_framework import serializers
from apps.production.models.module_work_break_record import ModuleWorkBreakRecord
from core.serializers.audit_serializer import AuditSerializer


class ModuleWorkBreakRecordSerializer(AuditSerializer):
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = ModuleWorkBreakRecord
        fields = "__all__"

    def get_duration_seconds(self, obj):
        if obj.start_time and obj.end_time:
            return int((obj.end_time - obj.start_time).total_seconds())
        return None
