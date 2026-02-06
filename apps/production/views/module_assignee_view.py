from rest_framework import viewsets
from apps.production.models import ModuleAssignee
from apps.production.serializers import ModuleAssigneeSerializer


class ModuleAssigneeViewSet(viewsets.ModelViewSet):
    queryset = ModuleAssignee.objects.all()
    serializer_class = ModuleAssigneeSerializer
