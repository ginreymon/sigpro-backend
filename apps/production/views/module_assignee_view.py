from core.views.base_model_view import BaseModelViewSet
from apps.production.models import ModuleAssignee
from apps.production.serializers import ModuleAssigneeSerializer


class ModuleAssigneeViewSet(BaseModelViewSet):
    queryset = ModuleAssignee.objects.all()
    serializer_class = ModuleAssigneeSerializer
