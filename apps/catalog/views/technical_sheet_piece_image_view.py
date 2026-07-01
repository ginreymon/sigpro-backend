from apps.production.views.local_base_model_view import LocalBaseModelViewSet
from apps.catalog.models.technical_sheet_piece_image import TechnicalSheetPieceImage
from apps.catalog.serializers import TechnicalSheetPieceImageSerializer


class TechnicalSheetPieceImageViewSet(LocalBaseModelViewSet):
    queryset = TechnicalSheetPieceImage.objects.all()
    serializer_class = TechnicalSheetPieceImageSerializer
    http_method_names = ['get', 'head', 'options']
