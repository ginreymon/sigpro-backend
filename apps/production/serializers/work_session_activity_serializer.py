from rest_framework import serializers
from apps.production.models import WorkSessionActivity
from apps.production.serializers.module_serializer import ModuleSerializer


class WorkSessionActivitySerializer(serializers.ModelSerializer):
    module = ModuleSerializer()
    duration = serializers.SerializerMethodField()

    class Meta:
        model = WorkSessionActivity
        fields = ["id", "module", "started_at", "ended_at", "duration"]

    def get_duration(self, obj):
        if obj.ended_at:
            return obj.ended_at - obj.started_at
        return None
