from rest_framework.viewsets import ModelViewSet


class BaseModelViewSet(ModelViewSet):
    search_fields = "__all__"
    filterset_fields = "__all__"
    ordering_fields = "__all__"
