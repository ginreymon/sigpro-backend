from core.views.base_model_view import BaseModelViewSet
from apps.production.models import WorkBreak
from apps.production.serializers import WorkBreakSerializer


class WorkBreakViewSet(BaseModelViewSet):
    queryset = WorkBreak.objects.all()
    serializer_class = WorkBreakSerializer
