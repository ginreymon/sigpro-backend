from apps.production.views.local_base_model_view import LocalBaseModelViewSet
from apps.catalog.models.sheet_measurement_detail import SheetMeasurementDetail
from apps.catalog.serializers import SheetMeasurementDetailSerializer


class SheetMeasurementDetailViewSet(LocalBaseModelViewSet):
    queryset = SheetMeasurementDetail.objects.all()
    serializer_class = SheetMeasurementDetailSerializer
    editable_fields = ['value']
