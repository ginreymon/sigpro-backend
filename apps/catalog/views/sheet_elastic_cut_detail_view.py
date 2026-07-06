from apps.production.views.local_base_model_view import LocalBaseModelViewSet
from apps.catalog.models.sheet_elastic_cut_detail import SheetElasticCutDetail
from apps.catalog.serializers import SheetElasticCutDetailSerializer


class SheetElasticCutDetailViewSet(LocalBaseModelViewSet):
    queryset = SheetElasticCutDetail.objects.all()
    serializer_class = SheetElasticCutDetailSerializer
    editable_fields = ['value']
