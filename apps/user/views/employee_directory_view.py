from core.views.base_model_view import BaseModelViewSet
from apps.production.models import EmployeeLocal
from apps.production.serializers import EmployeeLocalSerializer


class EmployeeDirectoryViewSet(BaseModelViewSet):
    """Directorio de empleados sin filtro de centro de costo, para administración de cuentas."""

    queryset = (
        EmployeeLocal.objects.filter(is_deleted=False).select_related("user_link__django_user")
    )
    serializer_class = EmployeeLocalSerializer
    http_method_names = ["get", "head", "options"]

    search_fields = [
        "first_name",
        "last_name1",
        "last_name2",
        "id_number",
        "user_link__django_user__username",
    ]
