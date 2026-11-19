from apps.production.models import WorkCenterLocal
from apps.production.serializers import WorkCenterLocalSerializer
from .local_base_model_view import LocalBaseModelViewSet
from core import option_keys as opt


class WorkCenterLocalViewSet(LocalBaseModelViewSet):
    write_options = (opt.MODULES, opt.GENERAL_CONFIG, opt.SEWING_CONFIG)

    queryset = WorkCenterLocal.objects.filter(is_deleted=False)
    serializer_class = WorkCenterLocalSerializer
