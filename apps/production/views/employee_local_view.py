from apps.production.models import EmployeeLocal, ProductionAreaCostCenter
from apps.production.serializers import EmployeeLocalSerializer
from .local_base_model_view import LocalBaseModelViewSet


class EmployeeLocalViewSet(LocalBaseModelViewSet):
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

        return queryset.filter(cost_center_rowid__in=cost_centers)