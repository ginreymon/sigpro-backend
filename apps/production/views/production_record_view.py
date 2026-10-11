from apps.production.models import ProductionRecord
from apps.production.serializers import ProductionRecordSerializer
from apps.production.views.op_record_view import OpRecordViewSet


class ProductionRecordViewSet(OpRecordViewSet):
    queryset = ProductionRecord.objects.all()
    serializer_class = ProductionRecordSerializer
    module_type = 'production'
