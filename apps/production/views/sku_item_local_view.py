from django.db.models import OuterRef, Subquery
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.production.models import SkuItemLocal, ReferenceSam
from apps.production.serializers import SkuItemLocalSerializer, SkuItemReferenceSerializer
from .local_base_model_view import LocalBaseModelViewSet

_REFERENCE_FIELDS = (
    "rowid_item", "reference", "description", "inv_type",
    "inventory_unit", "order_unit", "packing_unit",
    "replenishment_time", "lot_size", "safety_stock",
    "status", "sku_status", "cost", "suggested_price",
    "brand", "line", "group", "subgroup", "classification",
    "sewing", "print_design", "license", "collection",
    "world", "channel", "promotion", "priority", "pieces_per_set",
    "sam_value",
)


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

    @action(detail=False, methods=["get"], url_path="references")
    def references(self, request):
        queryset = self.filter_queryset(self.get_queryset()).values(*_REFERENCE_FIELDS).distinct()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SkuItemReferenceSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = SkuItemReferenceSerializer(queryset, many=True)
        return Response(serializer.data)
