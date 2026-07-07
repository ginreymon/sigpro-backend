from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import StampingReferenceSam
from apps.stamping.serializers import StampingReferenceSamSerializer


class StampingReferenceSamViewSet(BaseModelViewSet):
    queryset = StampingReferenceSam.objects.all()
    serializer_class = StampingReferenceSamSerializer
