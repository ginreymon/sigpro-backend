from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import StampingMachineType
from apps.stamping.serializers import StampingMachineTypeSerializer
from core import option_keys as opt


class StampingMachineTypeViewSet(BaseModelViewSet):
    write_options = (opt.MACHINES_CONFIG,)

    queryset = StampingMachineType.objects.all()
    serializer_class = StampingMachineTypeSerializer
    search_fields = ['name']
