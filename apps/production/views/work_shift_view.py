from core.views.base_model_view import BaseModelViewSet
from apps.production.models import WorkShift
from apps.production.serializers import WorkShiftSerializer


class WorkShiftViewSet(BaseModelViewSet):
    queryset = WorkShift.objects.all()
    serializer_class = WorkShiftSerializer

    search_fields = ["name", "start_time", "end_time"]
