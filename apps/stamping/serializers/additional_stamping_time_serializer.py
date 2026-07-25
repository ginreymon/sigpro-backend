from rest_framework import serializers
from core.serializers.audit_serializer import AuditSerializer
from apps.stamping.models import AdditionalStampingTime


class AdditionalStampingTimeSerializer(AuditSerializer):

    machine_name = serializers.SerializerMethodField()
    machine_type_name = serializers.SerializerMethodField()

    class Meta:
        model = AdditionalStampingTime
        fields = '__all__'

    def get_machine_name(self, obj):
        return obj.machine.name if obj.machine else None

    def get_machine_type_name(self, obj):
        return obj.machine_type.name if obj.machine_type else None
