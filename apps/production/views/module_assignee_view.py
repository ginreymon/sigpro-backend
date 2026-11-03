from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import ModuleAssignee
from apps.production.serializers import ModuleAssigneeSerializer


class ModuleAssigneeViewSet(AuditModelViewSet):
    queryset = ModuleAssignee.objects.select_related(
        "employee",
        "module__work_center",
        "module__location",
        "module__stamping_machine_assignment__machine",
    ).prefetch_related("module__assigned_users__user")
    serializer_class = ModuleAssigneeSerializer

    search_fields = [
        "employee__first_name",
        "employee__last_name1",
        "employee__last_name2",
        "employee__id_number",
        "module__name",
    ]

    def get_queryset(self):
        return super().get_queryset().filter(
            employee__is_deleted=False,
            employee__is_active=True,
        )
