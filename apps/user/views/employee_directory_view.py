from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from core.permissions import has_option_access
from core.views.base_model_view import BaseModelViewSet
from apps.people.models import EmployeeLocal
from apps.people.serializers import EmployeeLocalSerializer
from core import option_keys as opt


class EmployeeDirectoryViewSet(BaseModelViewSet):
    """Employee directory without cost-center filter, used for account administration."""

    read_options = (opt.USERS,)

    queryset = (
        EmployeeLocal.objects.filter(is_deleted=False).select_related("user_link__auth_user")
    )
    serializer_class = EmployeeLocalSerializer
    http_method_names = ["get", "head", "options"]

    search_fields = [
        "first_name",
        "last_name1",
        "last_name2",
        "id_number",
        "user_link__auth_user__username",
    ]

    @action(detail=False, methods=["get"], url_path="available", pagination_class=None)
    def available(self, request):
        if not has_option_access(request.user, "users"):
            raise PermissionDenied("No tiene permisos para realizar esta acción.")
        """Employees without an account, plus the one linked to `include_user` (edit form)."""
        condition = Q(user_link__isnull=True)
        include_user = request.query_params.get("include_user")
        if include_user and include_user.isdigit():
            condition |= Q(user_link__auth_user_id=int(include_user))
        queryset = self.get_queryset().filter(condition)
        return Response(self.get_serializer(queryset, many=True).data)
