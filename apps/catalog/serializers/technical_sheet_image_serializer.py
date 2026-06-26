from core.serializers.audit_serializer import AuditSerializer
from apps.catalog.models.technical_sheet_image import TechnicalSheetImage


class TechnicalSheetImageSerializer(AuditSerializer):
    class Meta:
        model = TechnicalSheetImage
        fields = '__all__'
