from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import ProductionRecord
from apps.production.serializers import ProductionRecordSerializer


class ProductionRecordViewSet(AuditModelViewSet):
    queryset = ProductionRecord.objects.all()
    serializer_class = ProductionRecordSerializer
