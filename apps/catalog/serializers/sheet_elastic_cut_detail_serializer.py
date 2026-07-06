from core.serializers.audit_serializer import AuditSerializer
from apps.catalog.models.sheet_elastic_cut_detail import SheetElasticCutDetail


class SheetElasticCutDetailSerializer(AuditSerializer):
    class Meta:
        model = SheetElasticCutDetail
        fields = '__all__'
