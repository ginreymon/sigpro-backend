from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import StampingPiece
from apps.stamping.serializers import StampingPieceSerializer
from core import option_keys as opt


class StampingPieceViewSet(BaseModelViewSet):
    write_options = (opt.MACHINES_CONFIG,)

    queryset = StampingPiece.objects.all()
    serializer_class = StampingPieceSerializer
