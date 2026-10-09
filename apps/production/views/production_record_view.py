from apps.production.models import ProductionRecord
from apps.production.serializers import ProductionRecordSerializer
from apps.common.views.op_record_view import OpRecordViewSet


class ProductionRecordViewSet(OpRecordViewSet):
    queryset = ProductionRecord.objects.all()
    serializer_class = ProductionRecordSerializer
    module_type = 'production'
