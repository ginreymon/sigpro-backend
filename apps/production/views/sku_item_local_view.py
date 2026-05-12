from django.db.models import OuterRef, Subquery
from apps.production.models import SkuItemLocal, ReferenceSam
from apps.production.serializers import SkuItemLocalSerializer
from .local_base_model_view import LocalBaseModelViewSet


class SkuItemLocalViewSet(LocalBaseModelViewSet):
    queryset = SkuItemLocal.objects.filter(is_deleted=False).annotate(
        sam_value=Subquery(
            ReferenceSam.objects.filter(rowid_item=OuterRef("rowid_item")).values("sam")[:1]
        )
    )
    serializer_class = SkuItemLocalSerializer

    search_fields = [
        "reference",
        "description",
        "barcode",
        "size",
        "color",
    ]
