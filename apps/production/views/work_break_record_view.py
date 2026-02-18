from core.views.base_model_view import BaseModelViewSet
from apps.production.models import WorkBreakRecord
from apps.production.serializers import WorkBreakRecordSerializer


class WorkBreakRecordViewSet(BaseModelViewSet):
    queryset = WorkBreakRecord.objects.all()
    serializer_class = WorkBreakRecordSerializer
