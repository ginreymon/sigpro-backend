from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import StampingPiece
from apps.stamping.serializers import StampingPieceSerializer


class StampingPieceViewSet(BaseModelViewSet):
    queryset = StampingPiece.objects.all()
    serializer_class = StampingPieceSerializer
