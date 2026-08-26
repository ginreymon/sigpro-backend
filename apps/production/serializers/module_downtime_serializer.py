from rest_framework import serializers
from apps.production.models.module_downtime import ModuleDowntime
from core.serializers.audit_serializer import AuditSerializer


class ModuleDowntimeSerializer(AuditSerializer):
    duration_seconds = serializers.SerializerMethodField()

    class Meta:
        model = ModuleDowntime
        fields = "__all__"

    def get_duration_seconds(self, obj):
        if obj.start_time and obj.end_time:
            return int((obj.end_time - obj.start_time).total_seconds())
        return None
