from core.views.base_model_view import BaseModelViewSet
from apps.production.models import Module
from apps.production.serializers import ModuleSerializer


class ModuleViewSet(BaseModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
