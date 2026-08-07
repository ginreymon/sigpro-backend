from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import StampingLayoutForm
from apps.stamping.serializers import StampingLayoutFormSerializer


class StampingLayoutFormViewSet(BaseModelViewSet):
    queryset = StampingLayoutForm.objects.all()
    serializer_class = StampingLayoutFormSerializer
