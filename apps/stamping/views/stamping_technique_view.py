from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import StampingTechnique
from apps.stamping.serializers import StampingTechniqueSerializer
from core import option_keys as opt


class StampingTechniqueViewSet(BaseModelViewSet):
    write_options = (opt.MACHINES_CONFIG,)

    queryset = StampingTechnique.objects.all()
    serializer_class = StampingTechniqueSerializer
