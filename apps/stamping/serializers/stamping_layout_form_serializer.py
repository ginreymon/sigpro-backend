from core.serializers.audit_serializer import AuditSerializer
from apps.stamping.models import StampingLayoutForm


class StampingLayoutFormSerializer(AuditSerializer):
    class Meta:
        model = StampingLayoutForm
        fields = '__all__'
