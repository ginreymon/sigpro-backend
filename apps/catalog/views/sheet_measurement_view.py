from apps.production.views.local_base_model_view import LocalBaseModelViewSet
from apps.catalog.models.sheet_measurement import SheetMeasurement
from apps.catalog.serializers import SheetMeasurementSerializer


class SheetMeasurementViewSet(LocalBaseModelViewSet):
    queryset = SheetMeasurement.objects.all()
    serializer_class = SheetMeasurementSerializer
    http_method_names = ['get', 'head', 'options']
