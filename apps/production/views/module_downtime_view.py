from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import ModuleDowntime
from apps.production.serializers import ModuleDowntimeSerializer


class ModuleDowntimeViewSet(AuditModelViewSet):
    queryset = ModuleDowntime.objects.all()
    serializer_class = ModuleDowntimeSerializer
