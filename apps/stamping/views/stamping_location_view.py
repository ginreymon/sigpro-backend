from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import StampingLocation
from apps.stamping.serializers import StampingLocationSerializer


class StampingLocationViewSet(BaseModelViewSet):
    queryset = StampingLocation.objects.all()
    serializer_class = StampingLocationSerializer
