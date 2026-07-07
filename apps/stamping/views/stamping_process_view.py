from core.views.base_model_view import BaseModelViewSet
from apps.stamping.models import StampingProcess
from apps.stamping.serializers import StampingProcessSerializer


class StampingProcessViewSet(BaseModelViewSet):
    queryset = StampingProcess.objects.all()
    serializer_class = StampingProcessSerializer
