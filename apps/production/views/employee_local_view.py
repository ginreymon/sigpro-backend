from apps.production.models import EmployeeLocal, ProductionArea
from apps.production.serializers import EmployeeLocalSerializer
from apps.production.constants import PRODUCTION_COST_CENTERS
from .local_base_model_view import LocalBaseModelViewSet


class EmployeeLocalViewSet(LocalBaseModelViewSet):
    queryset = (
        EmployeeLocal.objects.filter(
            is_deleted=False, cost_center_rowid__in=PRODUCTION_COST_CENTERS
        ).select_related("user_link__django_user")
    )
    serializer_class = EmployeeLocalSerializer

    search_fields = [
        "first_name",
        "last_name1",
        "last_name2",
        "id_number",
        "user_link__django_user__username"
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        core_module_id = self.request.query_params.get("core_module_id")
        if not core_module_id:
            return queryset

        cost_centers = ProductionArea.objects.filter(
            core_module_id=core_module_id
        ).values_list("cost_centers", flat=True).first()
        if not cost_centers:
            return queryset.none()

        return queryset.filter(cost_center_rowid__in=cost_centers)