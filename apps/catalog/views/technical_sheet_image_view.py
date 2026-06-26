from apps.production.views.local_base_model_view import LocalBaseModelViewSet
from apps.catalog.models.technical_sheet_image import TechnicalSheetImage
from apps.catalog.serializers import TechnicalSheetImageSerializer


class TechnicalSheetImageViewSet(LocalBaseModelViewSet):
    queryset = TechnicalSheetImage.objects.all()
    serializer_class = TechnicalSheetImageSerializer
    http_method_names = ['get', 'head', 'options']
