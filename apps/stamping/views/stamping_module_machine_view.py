from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import StampingModuleMachine
from apps.stamping.serializers import StampingModuleMachineSerializer
from core import option_keys as opt


class StampingModuleMachineViewSet(BaseModelViewSet):
    write_options = (opt.MACHINES_CONFIG,)

    queryset = StampingModuleMachine.objects.select_related('module', 'machine').all()
    serializer_class = StampingModuleMachineSerializer
    search_fields = ['module__name', 'machine__name']
    filterset_fields = ['module', 'machine', 'is_active', 'created_by', 'updated_by']
