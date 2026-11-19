from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import ModuleAssignee
from apps.production.serializers import ModuleAssigneeSerializer
from core import option_keys as opt


class ModuleAssigneeViewSet(AuditModelViewSet):
    write_options = (opt.MODULES, opt.GENERAL_CONFIG, opt.SEWING_CONFIG)

    queryset = ModuleAssignee.objects.all()
    serializer_class = ModuleAssigneeSerializer

    def get_queryset(self):
        return super().get_queryset().filter(
            employee__is_deleted=False,
            employee__is_active=True,
        )
