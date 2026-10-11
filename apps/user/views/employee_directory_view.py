from core.views.base_model_view import BaseModelViewSet
from apps.user.employee import get_employee_model, get_employee_serializer_class


class EmployeeDirectoryViewSet(BaseModelViewSet):
    """Directorio de empleados sin filtro de centro de costo, para administración de cuentas."""

    queryset = (
        get_employee_model().objects.filter(is_deleted=False).select_related("user_link__auth_user")
    )
    serializer_class = get_employee_serializer_class()
    http_method_names = ["get", "head", "options"]

    search_fields = [
        "first_name",
        "last_name1",
        "last_name2",
        "id_number",
        "user_link__auth_user__username",
    ]
