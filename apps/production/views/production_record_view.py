from rest_framework.decorators import action

from core.utils.date_utils import to_utc_naive
from core.views.audit_model_view import AuditModelViewSet
from core.views.recent_records_view import RecentRecordsMixin
from apps.production.models import ProductionRecord, WorkSession, WorkShiftSnapshot
from apps.production.repositories.productivity_repository import ProductivityRepository
from apps.production.serializers import ProductionRecordSerializer
from apps.production.services.work_session_service import shift_start_utc


class ProductionRecordViewSet(RecentRecordsMixin, AuditModelViewSet):
    queryset = ProductionRecord.objects.all()
    serializer_class = ProductionRecordSerializer

    recent_records_user_filter = 'work_session_activity__work_session__user'
    recent_records_select_related = ('work_session_activity',)
    recent_records_dedup_field = 'op_rowid'

    @action(detail=False, methods=["post"], url_path="manual-duration")
    def manual_duration(self, request, *args, **kwargs):
        """
        POST /production-records/manual-duration/

        Mantiene el endpoint por compatibilidad, pero se comporta igual que
        el create() normal (POST /production-records/).
        """
        work_session = WorkSession.objects.filter(user=request.user, is_closed=False).first()

        indicators = None
        if work_session:
            shift_snapshot = (
                WorkShiftSnapshot.objects.filter(work_session=work_session)
                .order_by("-id")
                .first()
            )
            shift_start_time = (
                shift_snapshot.start_time
                if shift_snapshot
                else work_session.work_shift.start_time
            )
            shift_end_time = (
                shift_snapshot.end_time
                if shift_snapshot
                else work_session.work_shift.end_time
            )

            activity = work_session.get_active_activity()
            if activity:
                fecha_inicio = to_utc_naive(
                    shift_start_utc(work_session, shift_start_time, shift_end_time)
                )
                indicators = ProductivityRepository.get_tiempos_operacion_modulo(
                    fecha_inicio,
                    activity.module_id,
                    work_session.work_shift_id,
                    tipo_modulo='production',
                )       

        response = self.create(request, *args, **kwargs)
        if indicators is not None:
            response.data['indicators'] = indicators
        return response      