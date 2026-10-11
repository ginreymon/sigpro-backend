from core.views.base_model_view import BaseModelViewSet
from django.contrib.auth.models import Group
from django.db.models import Count
from apps.user.serializers.group_serializer import GroupSerializer
from rest_framework.response import Response
from rest_framework import status
from core.exceptions import error_response


class GroupViewSet(BaseModelViewSet):
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
        if group.user_set.exists():
            return error_response(
                "No se puede eliminar el rol porque tiene usuarios asignados.", code="role_has_users",
            )
        return super().destroy(request, *args, **kwargs)