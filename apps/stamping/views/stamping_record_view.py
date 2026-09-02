from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError

from core.views.audit_model_view import AuditModelViewSet
from core.views.recent_records_view import RecentRecordsMixin
from apps.production.services.production_record_service import (
    active_work_session_and_activity,
    manual_duration_indicators,
    perform_manual_duration_batch,
    validate_manual_duration_budget,
)
from apps.stamping.models.stamping_record import StampingRecord
from apps.stamping.serializers import StampingRecordSerializer


class StampingRecordViewSet(RecentRecordsMixin, AuditModelViewSet):
    queryset = StampingRecord.objects.all()
    serializer_class = StampingRecordSerializer

    recent_records_user_filter = 'work_session_activity__work_session__user'
    recent_records_select_related = ('work_session_activity',)
    recent_records_dedup_field = 'op_rowid'

    @action(detail=False, methods=["post"], url_path="manual-duration")
    def manual_duration(self, request, *args, **kwargs):
        """
        POST /stamping-records/manual-duration/

        Mantiene el endpoint por compatibilidad, pero se comporta igual que
        el create() normal (POST /stamping-records/).
        """
        work_session, activity = active_work_session_and_activity(request)
        indicators = manual_duration_indicators(work_session, activity, tipo_modulo='stamping')

        if indicators:
            duration_seconds = request.data.get('duration_seconds')
            if duration_seconds is None:
                raise ValidationError({'duration_seconds': 'Este campo es requerido.'})
            validate_manual_duration_budget(indicators, float(duration_seconds))

        response = self.create(request, *args, **kwargs)
        if indicators is not None:
            response.data['indicators'] = indicators
        return response

    @action(detail=False, methods=["post"], url_path="manual-duration-batch")
    def manual_duration_batch(self, request):
        """
        POST /stamping-records/manual-duration-batch/

        Homólogo a production-records/manual-duration-batch/ (ver
        perform_manual_duration_batch) para registros de estampación.
        """
        return perform_manual_duration_batch(self, request, tipo_modulo='stamping')
