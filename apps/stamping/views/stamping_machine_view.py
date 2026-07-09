from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import StampingMachine
from apps.stamping.serializers import StampingMachineSerializer


class StampingMachineViewSet(BaseModelViewSet):
    queryset = StampingMachine.objects.select_related('machine_type').all()
    serializer_class = StampingMachineSerializer
    search_fields = ['name', 'machine_type__name']
