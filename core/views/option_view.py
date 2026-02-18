from core.views.base_model_view import BaseModelViewSet
from core.models import Option
from core.serializers.option_serializer import OptionSerializer


class OptionViewSet(BaseModelViewSet):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer
