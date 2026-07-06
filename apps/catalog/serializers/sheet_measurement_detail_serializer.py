from core.serializers.audit_serializer import AuditSerializer
from apps.catalog.models.sheet_measurement_detail import SheetMeasurementDetail


class SheetMeasurementDetailSerializer(AuditSerializer):
    class Meta:
        model = SheetMeasurementDetail
        fields = '__all__'
