from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import StampingMachine
from apps.stamping.serializers import StampingMachineSerializer
from core import option_keys as opt


class StampingMachineViewSet(BaseModelViewSet):
    write_options = (opt.MACHINES_CONFIG,)

    queryset = StampingMachine.objects.select_related('machine_type').all()
    serializer_class = StampingMachineSerializer
    search_fields = ['name', 'machine_type__name']
