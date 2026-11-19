from django.db.models import Prefetch
from apps.production.models import ModuleAssignee, ProductionAreaCostCenter
from apps.production.serializers.employee_last_module_serializer import (
    EmployeeWithLastModuleSerializer,
)
from apps.people.models import EmployeeLocal
from apps.people.serializers import EmployeeLocalSerializer
from .local_base_model_view import LocalBaseModelViewSet
from core import option_keys as opt


class EmployeeLocalViewSet(LocalBaseModelViewSet):
    write_options = (opt.MODULES, opt.GENERAL_CONFIG, opt.SEWING_CONFIG)

    queryset = EmployeeLocal.objects.filter(is_deleted=False).select_related(
        "user_link__auth_user"
    )
    serializer_class = EmployeeLocalSerializer

    search_fields = [
        "first_name",
        "last_name1",
        "last_name2",
        "id_number",
        "user_link__auth_user__username"
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        core_module_id = self.request.query_params.get("core_module_id")
        if not core_module_id:
            return queryset.none()

        cost_centers = ProductionAreaCostCenter.objects.filter(
            production_area__core_module_id=core_module_id
        ).values_list("cost_center_rowid", flat=True)
        if not cost_centers:
            return queryset.none()

        # One extra query for all employees: latest active-module assignment first.
        return queryset.filter(cost_center_rowid__in=cost_centers).prefetch_related(
            Prefetch(
                "moduleassignee_set",
                queryset=ModuleAssignee.objects.filter(module__is_active=True)
                .select_related("module")
                .order_by("-updated_at", "-created_at", "-id"),
                to_attr="last_module_assignments",
            )
        )

    def get_serializer_class(self):
        # `last_module` is added only when core_module_id is sent (list/all).
        if self.request and self.request.query_params.get("core_module_id"):
            return EmployeeWithLastModuleSerializer
        return super().get_serializer_class()