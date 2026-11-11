from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import Module, ModuleAssignee
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
            if assigned_module and queryset.filter(pk=assigned_module.module_id).exists():
                queryset = queryset.filter(pk=assigned_module.module_id)

        return queryset

    # DELETE /modules/{id}/employees/{employee_id}/ — used when the user has no open
    # session; with one, the work session PUT keeps the session consistent.
    @action(detail=True, methods=["delete"], url_path=r"employees/(?P<employee_id>\d+)")
    def remove_employee(self, request, pk=None, employee_id=None):
        deleted, _ = ModuleAssignee.objects.filter(module=self.get_object(), employee_id=employee_id).delete()
        if not deleted:
            raise NotFound("El empleado no está asignado a este módulo.")
        return Response(status=204)
