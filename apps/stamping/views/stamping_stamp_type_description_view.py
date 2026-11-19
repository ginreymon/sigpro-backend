from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import StampingStampTypeDescription
from apps.stamping.serializers import StampingStampTypeDescriptionSerializer
from core import option_keys as opt


class StampingStampTypeDescriptionViewSet(BaseModelViewSet):
    write_options = (opt.MACHINES_CONFIG,)

    queryset = StampingStampTypeDescription.objects.all()
    serializer_class = StampingStampTypeDescriptionSerializer
