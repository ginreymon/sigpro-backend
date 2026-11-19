from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import StampingLocation
from apps.stamping.serializers import StampingLocationSerializer
from core import option_keys as opt


class StampingLocationViewSet(BaseModelViewSet):
    write_options = (opt.MACHINES_CONFIG,)

    queryset = StampingLocation.objects.all()
    serializer_class = StampingLocationSerializer
