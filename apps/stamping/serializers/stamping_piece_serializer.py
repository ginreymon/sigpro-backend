from core.serializers.audit_serializer import AuditSerializer
from apps.stamping.models import StampingPiece


class StampingPieceSerializer(AuditSerializer):
    class Meta:
        model = StampingPiece
        fields = '__all__'
