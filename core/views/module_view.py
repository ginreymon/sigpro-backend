from rest_framework.viewsets import ModelViewSet
from core.models.module import Module
from core.serializers.module_serializer import ModuleSerializer


class ModuleViewSet(ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
