from apps.production.models.production_record import ProductionRecord
from core.serializers.audit_serializer import AuditSerializer


class ProductionRecordSerializer(AuditSerializer):
    class Meta:
        model = ProductionRecord
        fields = "__all__"
