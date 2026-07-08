from core.serializers.audit_serializer import AuditSerializer
from apps.stamping.models import StampingMachineType


class StampingMachineTypeSerializer(AuditSerializer):
    class Meta:
        model = StampingMachineType
        fields = '__all__'
