from rest_framework.viewsets import ModelViewSet
from core.models import Option
from core.serializers.option_serializer import OptionSerializer


class OptionViewSet(ModelViewSet):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer
