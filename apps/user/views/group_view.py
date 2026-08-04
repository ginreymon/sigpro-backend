from core.views.base_model_view import BaseModelViewSet
from django.contrib.auth.models import Group
from apps.user.serializers.group_serializer import GroupSerializer
from rest_framework.response import Response
from rest_framework import status


class GroupViewSet(BaseModelViewSet):
    queryset = Group.objects.prefetch_related("permissions", "group_options__option").all()
    serializer_class = GroupSerializer

    search_fields = [
        "name"
    ]

    def destroy(self, request, *args, **kwargs):
        group = self.get_object()
        if group.user_set.exists():
            return Response(
                {"detail": "No se puede eliminar el rol porque tiene usuarios asignados."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)