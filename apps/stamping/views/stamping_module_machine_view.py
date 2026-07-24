from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import StampingModuleMachine
from apps.stamping.serializers import StampingModuleMachineSerializer


class StampingModuleMachineViewSet(BaseModelViewSet):
    queryset = StampingModuleMachine.objects.select_related('module', 'machine').all()
    serializer_class = StampingModuleMachineSerializer
    search_fields = ['module__name', 'machine__name']
    filterset_fields = ['module', 'machine', 'is_active', 'created_by', 'updated_by']
