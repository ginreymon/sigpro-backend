from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import StampingMachineType
from apps.stamping.serializers import StampingMachineTypeSerializer


class StampingMachineTypeViewSet(BaseModelViewSet):
    queryset = StampingMachineType.objects.all()
    serializer_class = StampingMachineTypeSerializer
