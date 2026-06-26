from core.serializers.audit_serializer import AuditSerializer
from apps.catalog.models.sheet_elastic_cut import SheetElasticCut


class SheetElasticCutSerializer(AuditSerializer):
    class Meta:
        model = SheetElasticCut
        fields = '__all__'
