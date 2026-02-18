from core.views.base_model_view import BaseModelViewSet
from apps.production.models import ProductionRecord
from apps.production.serializers import ProductionRecordSerializer


class ProductionRecordViewSet(BaseModelViewSet):
    queryset = ProductionRecord.objects.all()
    serializer_class = ProductionRecordSerializer
