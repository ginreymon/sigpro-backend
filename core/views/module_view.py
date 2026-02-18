from core.views.base_model_view import BaseModelViewSet
from core.models.module import Module
from core.serializers.module_serializer import ModuleSerializer


class ModuleViewSet(BaseModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
