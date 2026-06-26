from django.db.models import OuterRef, Q, Subquery

from rest_framework.response import Response

from apps.production.views.local_base_model_view import LocalBaseModelViewSet
from apps.production.models.sku_item_local import SkuItemLocal
from apps.catalog.models.technical_sheet import TechnicalSheet
from apps.catalog.models.collection import Collection
from apps.catalog.serializers import TechnicalSheetSerializer


class TechnicalSheetViewSet(LocalBaseModelViewSet):
    queryset = TechnicalSheet.objects.select_related('status').all()
    serializer_class = TechnicalSheetSerializer
    http_method_names = ['get', 'head', 'options']
    search_fields = []

    def get_queryset(self):
        sku_base = SkuItemLocal.objects.filter(
            rowid_item=OuterRef('rowid_item'),
            is_deleted=False,
            is_active=True,
        )
        return super().get_queryset().annotate(
            sku_reference=Subquery(sku_base.values('reference')[:1]),
        ).order_by('sku_reference', '-created_at', 'status__name', 'sheet_version')

    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)
        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(status__name__icontains=search) |
                Q(rowid_item__in=SkuItemLocal.objects.filter(
                    is_deleted=False,
                    is_active=True,
                ).filter(
                    Q(reference__icontains=search) | Q(description__icontains=search)
                ).values('rowid_item'))
            )
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        items = page if page is not None else queryset

        rowid_items = [obj.rowid_item for obj in items]
        skus = (
            SkuItemLocal.objects
            .filter(rowid_item__in=rowid_items, is_deleted=False, is_active=True)
            .order_by('rowid_item', 'size')
        )

        sku_map = {}
        sizes_map = {}
        for sku in skus:
            if sku.rowid_item not in sku_map:
                sku_map[sku.rowid_item] = sku
            if sku.size and sku.size.strip():
                sizes_map.setdefault(sku.rowid_item, [])
                size = sku.size.strip()
                if size not in sizes_map[sku.rowid_item]:
                    sizes_map[sku.rowid_item].append(size)

        collection_rowids = [obj.collection_rowid for obj in items if obj.collection_rowid]
        collection_map = {
            c.rowid: c
            for c in Collection.objects.filter(rowid__in=collection_rowids, is_deleted=False)
        }

        context = {**self.get_serializer_context(), 'sku_map': sku_map, 'sizes_map': sizes_map, 'collection_map': collection_map}
        serializer = self.get_serializer(items, many=True, context=context)

        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)
