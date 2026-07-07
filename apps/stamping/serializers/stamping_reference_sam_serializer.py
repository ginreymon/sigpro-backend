from core.serializers.audit_serializer import AuditSerializer
from apps.stamping.models import StampingReferenceSam


class StampingReferenceSamSerializer(AuditSerializer):
    class Meta:
        model = StampingReferenceSam
        fields = '__all__'
