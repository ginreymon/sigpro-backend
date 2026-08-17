from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import Module
from apps.production.serializers import ModuleSerializer


class ModuleViewSet(AuditModelViewSet):
    queryset = Module.objects.select_related(
        "work_center", "location", "stamping_machine_assignment", "stamping_machine_assignment__machine"
    ).prefetch_related("assigned_users__user")
    serializer_class = ModuleSerializer

    search_fields = [
        "name",
        "number",
        "operator_count",
        "location__name",
        "work_center__description",
        "work_center__code",
        "work_center__short_description",
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        core_module_id = self.request.query_params.get("core_module_id")
        if core_module_id:
            queryset = queryset.filter(location__core_module_id=core_module_id)

        for_day_operation = self.request.query_params.get("for_day_operation")
        if for_day_operation:
            assigned_module = getattr(self.request.user, "assigned_module", None)
            if assigned_module:
                queryset = queryset.filter(assigned_users__user=self.request.user)

        return queryset
