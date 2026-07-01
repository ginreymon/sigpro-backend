from core.serializers.audit_serializer import AuditSerializer
from apps.catalog.models.technical_sheet_piece_image import TechnicalSheetPieceImage


class TechnicalSheetPieceImageSerializer(AuditSerializer):
    class Meta:
        model = TechnicalSheetPieceImage
        fields = '__all__'
