from apps.production.models import WorkCenterLocal
from apps.production.serializers import WorkCenterLocalSerializer
from .local_base_model_view import LocalBaseModelViewSet


class WorkCenterLocalViewSet(LocalBaseModelViewSet):
    queryset = WorkCenterLocal.objects.all()
    serializer_class = WorkCenterLocalSerializer
