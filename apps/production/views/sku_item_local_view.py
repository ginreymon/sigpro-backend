from apps.production.models import SkuItemLocal
from apps.production.serializers import SkuItemLocalSerializer
from .local_base_model_view import LocalBaseModelViewSet


class SkuItemLocalViewSet(LocalBaseModelViewSet):
    queryset = SkuItemLocal.objects.filter(is_deleted=False)
    serializer_class = SkuItemLocalSerializer

    search_fields = [
        "reference",
        "description",
        "barcode",
        "size",
        "color",
    ]
