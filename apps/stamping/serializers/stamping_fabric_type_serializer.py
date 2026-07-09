from core.serializers.audit_serializer import AuditSerializer
from apps.stamping.models import StampingFabricType


class StampingFabricTypeSerializer(AuditSerializer):
    class Meta:
        model = StampingFabricType
        fields = '__all__'
