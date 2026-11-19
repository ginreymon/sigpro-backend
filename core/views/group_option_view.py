from core.views.base_model_view import BaseModelViewSet
from core.models.group_option import GroupOption
from core.serializers.group_option_serializer import GroupOptionSerializer
from core import option_keys as opt


class GroupOptionViewSet(BaseModelViewSet):
    write_options = (opt.ROLES,)
    read_options = (opt.ROLES,)

    queryset = GroupOption.objects.all()
    serializer_class = GroupOptionSerializer
