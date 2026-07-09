from core.serializers.audit_serializer import AuditSerializer
from apps.stamping.models import StampingStampTypeDescription


class StampingStampTypeDescriptionSerializer(AuditSerializer):
    class Meta:
        model = StampingStampTypeDescription
        fields = '__all__'
