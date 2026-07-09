from core.serializers.audit_serializer import AuditSerializer
from apps.stamping.models import StampingTechnique


class StampingTechniqueSerializer(AuditSerializer):
    class Meta:
        model = StampingTechnique
        fields = '__all__'
