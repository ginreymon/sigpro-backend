from django.db.models import CharField, OuterRef, Subquery
from rest_framework.response import Response
from core.views.base_model_view import BaseModelViewSet
from apps.production.models import SkuItemLocal
from apps.stamping.models import StampingReferenceSam
from apps.stamping.serializers import StampingReferenceSamSerializer


class StampingReferenceSamViewSet(BaseModelViewSet):
    queryset = StampingReferenceSam.objects.annotate(
        reference=Subquery(
            SkuItemLocal.objects.filter(
                rowid_item=OuterRef("rowid_item"),
                is_deleted=False,
            ).order_by().values("reference")[:1],
            output_field=CharField(),
        ),
    )
    serializer_class = StampingReferenceSamSerializer
    search_fields = ["reference_code", "reference"]

    def _serializer_context_with_skus(self, objs):
        rowid_items = {obj.rowid_item for obj in objs}
        context = self.get_serializer_context()
        context['sku_map'] = SkuItemLocal.map_by_rowid_item(rowid_items)
        return context

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        objs = page if page is not None else queryset
        serializer = self.get_serializer(
            objs, many=True, context=self._serializer_context_with_skus(objs)
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, context=self._serializer_context_with_skus([instance])
        )
        return Response(serializer.data)
