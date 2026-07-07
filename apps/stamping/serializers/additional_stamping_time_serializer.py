from core.serializers.audit_serializer import AuditSerializer
from apps.stamping.models import AdditionalStampingTime


class AdditionalStampingTimeSerializer(AuditSerializer):
    class Meta:
        model = AdditionalStampingTime
        fields = '__all__'
