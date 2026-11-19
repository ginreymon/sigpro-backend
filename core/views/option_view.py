from core.views.base_model_view import BaseModelViewSet
from core.models import Option
from core.serializers.option_serializer import OptionSerializer
from core import option_keys as opt


class OptionViewSet(BaseModelViewSet):
    write_options = (opt.ROLES,)

    queryset = Option.objects.all()
    serializer_class = OptionSerializer
