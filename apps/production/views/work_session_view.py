from core.views.base_model_view import BaseModelViewSet
from apps.production.models import WorkSession
from apps.production.serializers import WorkSessionSerializer


class WorkSessionViewSet(BaseModelViewSet):
    queryset = WorkSession.objects.all()
    serializer_class = WorkSessionSerializer
