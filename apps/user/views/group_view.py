from core.views.base_model_view import BaseModelViewSet
from django.contrib.auth.models import Group
from django.db.models import Count
from apps.user.serializers.group_serializer import GroupSerializer
from core.permissions import other_role_managers, roles_option_ids
from core.models.group_option import GroupOption
from core.exceptions import error_response
from core import option_keys as opt


class GroupViewSet(BaseModelViewSet):
    write_options = (opt.ROLES,)
    read_options = (opt.ROLES,)

    queryset = Group.objects.prefetch_related(
        "permissions", "group_options__option"
    ).select_related(
        "home_view_link__home_view"
    ).annotate(user_count=Count("user", distinct=True))
    serializer_class = GroupSerializer

    search_fields = [
        "name"
    ]

    def destroy(self, request, *args, **kwargs):
        group = self.get_object()
        if GroupOption.objects.filter(group=group, option_id__in=list(roles_option_ids())).exists()                 and not other_role_managers(group).exists():
            return error_response(
                "No se puede eliminar el último rol con acceso a Roles.", code="last_roles_admin",
            )
        if group.user_set.exists():
            return error_response(
                "No se puede eliminar el rol porque tiene usuarios asignados.", code="role_has_users",
            )
        return super().destroy(request, *args, **kwargs)