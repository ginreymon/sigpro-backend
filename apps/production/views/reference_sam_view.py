from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from django.db.models import Count, IntegerField, OuterRef, Subquery
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
        reference=SkuItemLocal.reference_subquery(),
    )
    serializer_class = ReferenceSamSerializer
    search_fields = ["rowid_item", "reference"]

    def get_object(self):
        try:
            return super().get_object()
        except Http404:
            pk = self.kwargs.get(self.lookup_field)
            queryset = self.filter_queryset(self.get_queryset())
            try:
                instance = queryset.get(rowid_item=pk)
            except ReferenceSam.DoesNotExist:
                raise Http404
            self.check_object_permissions(self.request, instance)
            return instance

    def create(self, request, *args, **kwargs):
        rowid_item = request.data.get("rowid_item")
        if rowid_item:
            raw = ReferenceSam.objects.filter(rowid_item=rowid_item).first()
            if raw:
                serializer = self.get_serializer(raw, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                instance = self.get_queryset().get(pk=raw.pk)
                return Response(self.get_serializer(instance).data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        saved = serializer.save()
        instance = self.get_queryset().get(pk=saved.pk)
        headers = self.get_success_headers(serializer.data)
        return Response(self.get_serializer(instance).data, status=status.HTTP_201_CREATED, headers=headers)
