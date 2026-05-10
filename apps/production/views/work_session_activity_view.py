from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import WorkSessionActivity
from apps.production.models.work_break import WorkBreak
from apps.production.models.work_break_record import WorkBreakRecord
from apps.production.serializers.work_session_activity_serializer import WorkSessionActivitySerializer
from apps.production.serializers.work_break_record_serializer import WorkBreakRecordSerializer


class WorkSessionActivityViewSet(AuditModelViewSet):
    queryset = WorkSessionActivity.objects.all()
    serializer_class = WorkSessionActivitySerializer

    filterset_fields = {
        "work_session": ["exact"],
        "module": ["exact"],
        "is_active": ["exact"],
    }

    def get_queryset(self):
        return (
            WorkSessionActivity.objects.all()
            .select_related("module", "work_session")
            .prefetch_related(
                "employee_snapshots__employee",
                "work_break_records",
                "production_records",
            )
        )

    # POST /work-session-activities/{id}/pause/
    # Payload: { "work_break": <id> }  OR  { "custom_reason": "texto" }
    @action(detail=True, methods=["post"], url_path="pause")
    def pause(self, request, pk=None):
        activity = self.get_object()

        if activity.is_paused:
            return Response(
                {"detail": "Activity is already paused."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        work_break_id = request.data.get("work_break")
        custom_reason = request.data.get("custom_reason")

        if not work_break_id and not custom_reason:
            return Response(
                {"detail": "Provide work_break or custom_reason."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()
        break_kwargs = {"work_session_activity": activity, "start_time": now}

        if work_break_id:
            try:
                work_break = WorkBreak.objects.get(pk=work_break_id)
            except WorkBreak.DoesNotExist:
                return Response(
                    {"detail": "WorkBreak not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            break_kwargs["work_break"] = work_break
        else:
            break_kwargs["custom_reason"] = custom_reason.strip()

        record = WorkBreakRecord(**break_kwargs)
        record.save()

        return Response(
            {
                "server_now": now,
                "server_end_pause": record.end_time,
                "work_break_record": WorkBreakRecordSerializer(record).data,
            },
            status=status.HTTP_201_CREATED,
        )

    # POST /work-session-activities/{id}/resume/
    @action(detail=True, methods=["post"], url_path="resume")
    def resume(self, request, pk=None):
        activity = self.get_object()
        active_break = activity.active_break

        if not active_break:
            return Response(
                {"detail": "Activity is not paused."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()
        active_break.end_time = now
        active_break.save()

        return Response(
            {
                "server_now": now,
                "work_break_record": WorkBreakRecordSerializer(active_break).data,
            },
            status=status.HTTP_200_OK,
        )
