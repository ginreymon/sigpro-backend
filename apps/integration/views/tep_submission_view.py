from django.db.models import Prefetch

from core.views.base_model_view import BaseModelViewSet
from apps.integration.models import TepDetail, TepSubmission
from apps.integration.serializers import TepSubmissionSerializer


class TepSubmissionViewSet(BaseModelViewSet):
    """Solo lectura: historial de los envíos hechos por `integration/tep/send/`
    con su resultado (status, error y respuesta de SIESA). Los envíos se crean
    únicamente desde ese endpoint."""

    queryset = (
        TepSubmission.objects.select_related('created_by', 'updated_by')
        .prefetch_related(Prefetch('details', queryset=TepDetail.objects.prefetch_related('records')))
    )
    serializer_class = TepSubmissionSerializer
    http_method_names = ['get', 'head', 'options']

    # created_at__gte / created_at__lt: date range of the submission (UTC datetimes).
    filterset_fields = {
        'status': ['exact'],
        'document_number': ['exact'],
        'work_center_id': ['exact'],
        'date': ['exact'],
        'created_at': ['gte', 'lt'],
    }
    search_fields = ['work_center_id', 'error_detail', 'details__op_document_number']
    ordering_fields = ['created_at', 'sent_at', 'status', 'date', 'document_number']
