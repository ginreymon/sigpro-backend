from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import WorkSessionActivity
from apps.production.repositories.work_session_repository import WorkSessionActivityRepository
from apps.production.serializers.work_session_activity_serializer import WorkSessionActivitySerializer
from apps.production.serializers.work_break_record_serializer import WorkBreakRecordSerializer
from apps.production.services import work_break_service
from apps.production.views.session_rule_error_mixin import SessionRuleErrorMixin


class WorkSessionActivityViewSet(SessionRuleErrorMixin, AuditModelViewSet):
    """Pause/resume rules live in work_break_service; this view only reads the
    request and serializes."""

    queryset = WorkSessionActivity.objects.all()
    serializer_class = WorkSessionActivitySerializer

    filterset_fields = {
        "work_session": ["exact"],
        "module": ["exact"],
        "is_active": ["exact"],
    }

    def get_queryset(self):
        return WorkSessionActivityRepository.detail_queryset()

    def _pause(self, request, *, auto_resume):
        record = work_break_service.pause(
            self.get_object(),
            request.user,
            work_break_id=request.data.get("work_break"),
            custom_reason=request.data.get("custom_reason"),
            work_break_minutes=request.data.get("work_break_minutes"),
            auto_resume=auto_resume,
        )
        return Response(WorkBreakRecordSerializer(record).data, status=status.HTTP_201_CREATED)

    # POST /work-session-activities/{id}/pause/
    # Payload: { "work_break": <id> }  OR  { "custom_reason": "texto" }
    #   OR (stamping) { "custom_reason": "texto", "work_break_minutes": <int> }
    @action(detail=True, methods=["post"], url_path="pause")
    def pause(self, request, pk=None):
        return self._pause(request, auto_resume=False)

    # POST /work-session-activities/{id}/pause-autoresume/
    # Espejo de /pause/: registra la pausa ya resuelta, calculando end_time y
    # resumed_at en el momento de la creación en vez de esperar un /resume/.
    # Payload: { "work_break": <id> }  OR  { "custom_reason": "texto", "work_break_minutes": <int> }
    @action(detail=True, methods=["post"], url_path="pause-autoresume")
    def pause_autoresume(self, request, pk=None):
        return self._pause(request, auto_resume=True)

    # POST /work-session-activities/{id}/resume/
    @action(detail=True, methods=["post"], url_path="resume")
    def resume(self, request, pk=None):
        record = work_break_service.resume(self.get_object())
        return Response(WorkBreakRecordSerializer(record).data, status=status.HTTP_200_OK)
