from rest_framework import serializers
from apps.production.models import WorkSessionActivity
from apps.production.serializers.module_serializer import ModuleSerializer
from apps.production.serializers.production_record_serializer import ProductionRecordSerializer


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
    
    def get_last_open_production_record(self, obj):
        record = obj.last_open_production_record

        if not record:
            return None

        return ProductionRecordSerializer(record).data
