from django.db.models import CharField, Count, IntegerField, OuterRef, Subquery
from apps.production.models import ReferenceSam, SkuItemLocal
from apps.production.serializers import ReferenceSamSerializer
from core.views.base_model_view import BaseModelViewSet


class ReferenceSamViewSet(BaseModelViewSet):
    queryset = ReferenceSam.objects.annotate(
        skus_count=Subquery(
            SkuItemLocal.objects.filter(
                rowid_item=OuterRef("rowid_item"),
                is_deleted=False,
            ).order_by().values("rowid_item").annotate(c=Count("id")).values("c")[:1],
            output_field=IntegerField(),
        ),
        reference=Subquery(
            SkuItemLocal.objects.filter(
                rowid_item=OuterRef("rowid_item"),
                is_deleted=False,
            ).order_by().values("reference")[:1],
            output_field=CharField(),
        ),
    )
    serializer_class = ReferenceSamSerializer

    search_fields = ["rowid_item", "reference"]
