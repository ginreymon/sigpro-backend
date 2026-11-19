from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import StampingProcess
from apps.stamping.serializers import StampingProcessSerializer
from core import option_keys as opt


class StampingProcessViewSet(BaseModelViewSet):
    write_options = (opt.MACHINES_CONFIG,)

    queryset = StampingProcess.objects.select_related('machine').all()
    serializer_class = StampingProcessSerializer
    search_fields = ['name', 'machine__name']
    filterset_fields = ['name', 'machine', 'is_active', 'created_by', 'updated_by']
