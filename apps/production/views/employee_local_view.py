from apps.production.models import EmployeeLocal
from apps.production.serializers import EmployeeLocalSerializer
from .local_base_model_view import LocalBaseModelViewSet


class EmployeeLocalViewSet(LocalBaseModelViewSet):
    queryset = (EmployeeLocal.objects.filter(is_deleted=False).select_related("user_link__django_user"))
    serializer_class = EmployeeLocalSerializer

    search_fields = [
        "first_name",
        "last_name1",
        "last_name2",
        "id_number",
        "user_link__django_user__username"    
    ] 