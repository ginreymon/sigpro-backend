from apps.production.views.local_base_model_view import LocalBaseModelViewSet
from apps.catalog.models.sheet_elastic_cut import SheetElasticCut
from apps.catalog.serializers import SheetElasticCutSerializer


class SheetElasticCutViewSet(LocalBaseModelViewSet):
    queryset = SheetElasticCut.objects.all()
    serializer_class = SheetElasticCutSerializer
    http_method_names = ['get', 'head', 'options']
