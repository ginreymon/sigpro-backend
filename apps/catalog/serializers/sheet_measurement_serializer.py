from core.serializers.audit_serializer import AuditSerializer
from apps.catalog.models.sheet_measurement import SheetMeasurement


class SheetMeasurementSerializer(AuditSerializer):
    class Meta:
        model = SheetMeasurement
        fields = '__all__'
