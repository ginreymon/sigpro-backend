from core.views.base_model_view import BaseModelViewSet
from apps.catalog.models.technical_sheet_status import TechnicalSheetStatus
from apps.catalog.serializers import TechnicalSheetStatusSerializer


class TechnicalSheetStatusViewSet(BaseModelViewSet):
    queryset = TechnicalSheetStatus.objects.all()
    serializer_class = TechnicalSheetStatusSerializer
    http_method_names = ['get', 'head', 'options']
