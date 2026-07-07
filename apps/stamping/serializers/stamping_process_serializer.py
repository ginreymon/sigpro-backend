from core.serializers.audit_serializer import AuditSerializer
from apps.stamping.models import StampingProcess


class StampingProcessSerializer(AuditSerializer):
    class Meta:
        model = StampingProcess
        fields = '__all__'
