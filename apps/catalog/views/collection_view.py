from core.views.base_model_view import BaseModelViewSet
from apps.catalog.models.collection import Collection
from apps.catalog.serializers import CollectionSerializer


class CollectionViewSet(BaseModelViewSet):
    queryset = Collection.objects.filter(is_deleted=False)
    serializer_class = CollectionSerializer
    http_method_names = ['get', 'head', 'options']
