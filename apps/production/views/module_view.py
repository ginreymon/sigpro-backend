from rest_framework import viewsets
from apps.production.models import Module
from apps.production.serializers import ModuleSerializer


class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
