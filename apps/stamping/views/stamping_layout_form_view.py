from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import StampingLayoutForm
from apps.stamping.serializers import StampingLayoutFormSerializer
from core import option_keys as opt


class StampingLayoutFormViewSet(BaseModelViewSet):
    write_options = (opt.MACHINES_CONFIG,)

    queryset = StampingLayoutForm.objects.all()
    serializer_class = StampingLayoutFormSerializer
