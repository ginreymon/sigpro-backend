from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import StampingTechnique
from apps.stamping.serializers import StampingTechniqueSerializer


class StampingTechniqueViewSet(BaseModelViewSet):
    queryset = StampingTechnique.objects.all()
    serializer_class = StampingTechniqueSerializer
