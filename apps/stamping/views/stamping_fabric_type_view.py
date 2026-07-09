from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import StampingFabricType
from apps.stamping.serializers import StampingFabricTypeSerializer


class StampingFabricTypeViewSet(BaseModelViewSet):
    queryset = StampingFabricType.objects.all()
    serializer_class = StampingFabricTypeSerializer
