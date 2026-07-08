from rest_framework import serializers
from core.serializers.audit_serializer import AuditSerializer
from apps.stamping.models import StampingMachine


class StampingMachineSerializer(AuditSerializer):

    machine_type_name = serializers.SerializerMethodField()

    class Meta:
        model = StampingMachine
        fields = '__all__'

    def get_machine_type_name(self, obj):
        return obj.machine_type.name if obj.machine_type else None
