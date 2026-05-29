from rest_framework.decorators import action
from rest_framework.response import Response
from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import ProductionRecord
from apps.production.serializers import ProductionRecordSerializer


class ProductionRecordViewSet(AuditModelViewSet):
    queryset = ProductionRecord.objects.all()
    serializer_class = ProductionRecordSerializer

    @action(detail=False, methods=['get'], url_path='last')
    def last(self, request):
        record = (
            ProductionRecord.objects
            .filter(work_session_activity__work_session__user=request.user)
            .select_related('work_session_activity')
            .prefetch_related('work_session_activity__work_break_records')
            .order_by('-updated_at')
            .first()
        )
        if not record:
            return Response(None)
        return Response(ProductionRecordSerializer(record, context={'request': request}).data)
