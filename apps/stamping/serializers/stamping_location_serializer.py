from core.serializers.audit_serializer import AuditSerializer
from apps.stamping.models import StampingLocation


class StampingLocationSerializer(AuditSerializer):
    class Meta:
        model = StampingLocation
        fields = '__all__'
