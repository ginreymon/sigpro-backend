from core.views.base_model_view import BaseModelViewSet
from core.models.group_option import GroupOption
from core.serializers.group_option_serializer import GroupOptionSerializer


class GroupOptionViewSet(BaseModelViewSet):
    queryset = GroupOption.objects.all()
    serializer_class = GroupOptionSerializer
