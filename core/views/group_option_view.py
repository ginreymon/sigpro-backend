from rest_framework.viewsets import ModelViewSet
from core.models.group_option import GroupOption
from core.serializers.group_option_serializer import GroupOptionSerializer


class GroupOptionViewSet(ModelViewSet):
    queryset = GroupOption.objects.all()
    serializer_class = GroupOptionSerializer
