from django.db.models import Max, Min, OuterRef, Subquery
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.production.models import SkuItemLocal, ReferenceSam
from apps.production.serializers import SkuItemLocalSerializer, SkuItemReferenceSerializer
from .local_base_model_view import LocalBaseModelViewSet


class SkuItemLocalViewSet(LocalBaseModelViewSet):
    queryset = SkuItemLocal.objects.filter(is_deleted=False).annotate(
        sam_value=Subquery(
            ReferenceSam.objects.filter(rowid_item=OuterRef("rowid_item")).values("sam")[:1]
        ),
        sam_id=Subquery(
            ReferenceSam.objects.filter(rowid_item=OuterRef("rowid_item")).values("id")[:1]
        ),
    )
    serializer_class = SkuItemLocalSerializer

    search_fields = [
        "reference",
        "description",
        "barcode",
        "size",
        "color",
        "sewing",
    ]

    @action(detail=False, methods=["get"], url_path="references")
    def references(self, request):
        base_qs = self.filter_queryset(SkuItemLocal.objects.filter(is_deleted=False))

        queryset = (
            base_qs
            .order_by()
            .values("rowid_item")
            .annotate(
                id=Min("rowid_item"),
                reference=Max("reference"),
                description=Max("description"),
                inv_type=Max("inv_type"),
                inventory_unit=Max("inventory_unit"),
                order_unit=Max("order_unit"),
                packing_unit=Max("packing_unit"),
                replenishment_time=Max("replenishment_time"),
                lot_size=Max("lot_size"),
                safety_stock=Max("safety_stock"),
                status=Max("status"),
                sku_status=Max("sku_status"),
                cost=Max("cost"),
                suggested_price=Max("suggested_price"),
                brand=Max("brand"),
                line=Max("line"),
                group=Max("group"),
                subgroup=Max("subgroup"),
                classification=Max("classification"),
                sewing=Max("sewing"),
                print_design=Max("print_design"),
                license=Max("license"),
                collection=Max("collection"),
                world=Max("world"),
                channel=Max("channel"),
                promotion=Max("promotion"),
                priority=Max("priority"),
                pieces_per_set=Max("pieces_per_set"),
                sam_value=Subquery(
                    ReferenceSam.objects.filter(rowid_item=OuterRef("rowid_item")).values("sam")[:1]
                ),
                sam_id=Subquery(
                    ReferenceSam.objects.filter(rowid_item=OuterRef("rowid_item")).values("id")[:1]
                ),
            )
            .order_by("rowid_item")
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SkuItemReferenceSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = SkuItemReferenceSerializer(queryset, many=True)
        return Response(serializer.data)
