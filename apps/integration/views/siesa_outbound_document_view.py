from core.views.base_model_view import BaseModelViewSet
from apps.integration.models import SiesaOutboundDocument
from apps.integration.serializers import SiesaOutboundDocumentSerializer


class SiesaOutboundDocumentViewSet(BaseModelViewSet):
    """Solo lectura: la tabla es un outbox transaccional inmutable, ver
    docstring de SiesaOutboundDocument. La UI solo consulta su estado."""

    queryset = SiesaOutboundDocument.objects.all()
    serializer_class = SiesaOutboundDocumentSerializer
    http_method_names = ['get', 'head', 'options']

    filterset_fields = ['status', 'document_type', 'op_number', 'work_center_code']
    search_fields = ['document_type', 'idempotency_key', 'work_center_code', 'error_detail']
    ordering_fields = ['created_at', 'updated_at', 'sent_at', 'attempts', 'status', 'op_number']
