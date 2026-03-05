from core.views.base_model_view import BaseModelViewSet
from django.contrib.auth.models import Group
from apps.user.serializers.group_serializer import GroupSerializer


class GroupViewSet(BaseModelViewSet):
    queryset = Group.objects.prefetch_related("permissions", "group_options__option").all()
    serializer_class = GroupSerializer

    search_fields = [
        "name"
    ]