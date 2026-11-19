from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import StampingFabricType
from apps.stamping.serializers import StampingFabricTypeSerializer
from core import option_keys as opt


class StampingFabricTypeViewSet(BaseModelViewSet):
    write_options = (opt.MACHINES_CONFIG,)

    queryset = StampingFabricType.objects.all()
    serializer_class = StampingFabricTypeSerializer
