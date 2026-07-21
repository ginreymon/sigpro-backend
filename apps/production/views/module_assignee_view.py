from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import ModuleAssignee
from apps.production.serializers import ModuleAssigneeSerializer


class ModuleAssigneeViewSet(AuditModelViewSet):
    queryset = ModuleAssignee.objects.all()
    serializer_class = ModuleAssigneeSerializer

    def get_queryset(self):
        return super().get_queryset().filter(
            employee__is_deleted=False,
            employee__is_active=True,
        )
