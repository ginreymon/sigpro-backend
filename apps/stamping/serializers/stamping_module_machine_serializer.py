from rest_framework import serializers
from core.serializers.audit_serializer import AuditSerializer
from apps.stamping.models import StampingModuleMachine


class StampingModuleMachineSerializer(AuditSerializer):

    module_name = serializers.SerializerMethodField()
    machine_name = serializers.SerializerMethodField()

    class Meta:
        model = StampingModuleMachine
        fields = '__all__'

    def get_module_name(self, obj):
        return obj.module.name if obj.module else None

    def get_machine_name(self, obj):
        return obj.machine.name if obj.machine else None
