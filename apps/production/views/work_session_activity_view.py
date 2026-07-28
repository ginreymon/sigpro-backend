import math
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import transaction
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

    def _already_paused_response(self, activity):
        detail = "La actividad ya está pausada. Debes reanudarla para continuar."
        active_break = activity.active_break

        if active_break and active_break.end_time:
            remaining_minutes = math.ceil(
                (active_break.end_time - timezone.now()).total_seconds() / 60
            )
            if remaining_minutes > 0:
                detail = f"La actividad está pausada. Faltan {remaining_minutes} minuto(s) para reanudar."
            else:
                detail = "El tiempo de pausa ya terminó. Reanuda la actividad para continuar."

        return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        return (
            WorkSessionActivity.objects.all()
            .select_related("module", "work_session")
            .prefetch_related(
                "work_break_records",
                "production_records",
            )
        )

    def _handle_pause(self, request, activity, *, auto_resume):
        if not activity.is_active:
            return Response({"detail": "La actividad no está activa."}, status=status.HTTP_400_BAD_REQUEST)

        if activity.work_session.is_closed:
            return Response({"detail": "La sesión está cerrada."}, status=status.HTTP_400_BAD_REQUEST)

        if activity.is_paused:
            return self._already_paused_response(activity)

        work_break_id = request.data.get("work_break")
        custom_reason = request.data.get("custom_reason")
        work_break_minutes = request.data.get("work_break_minutes")

        if not work_break_id and not custom_reason:
            return Response(
                {"detail": "Debe indicar un tipo de pausa o un motivo personalizado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if auto_resume and not work_break_id and work_break_minutes is None:
            return Response(
                {"detail": "Debe indicar work_break_minutes para calcular el auto-resume del motivo personalizado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if work_break_minutes is not None:
            try:
                work_break_minutes = int(work_break_minutes)
            except (TypeError, ValueError):
                return Response(
                    {"detail": "Los minutos deben ser un número entero."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if work_break_minutes < 1:
                return Response(
                    {"detail": "Los minutos deben ser mayores a 0."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        now = timezone.now()
        break_kwargs = {
            "work_session_activity": activity,
            "start_time": now,
            "created_by": request.user,
            "updated_by": request.user,
        }

        if work_break_id:
            try:
                work_break = WorkBreak.objects.get(pk=work_break_id)
            except WorkBreak.DoesNotExist:
                return Response(
                    {"detail": "El tipo de pausa no existe."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            break_kwargs["work_break"] = work_break
        else:
            break_kwargs["custom_reason"] = custom_reason.strip()

        record = WorkBreakRecord(**break_kwargs)

        if work_break_minutes is not None and not work_break_id:
            record.end_time = now + timezone.timedelta(minutes=work_break_minutes)

        record.save()

        if auto_resume:
            record.resumed_at = record.end_time
            record.save()

        return Response(
            WorkBreakRecordSerializer(record).data,
            status=status.HTTP_201_CREATED,
        )

    # POST /work-session-activities/{id}/pause/
    # Payload: { "work_break": <id> }  OR  { "custom_reason": "texto" }
    #   OR (stamping) { "custom_reason": "texto", "work_break_minutes": <int> }
    @action(detail=True, methods=["post"], url_path="pause")
    @transaction.atomic
    def pause(self, request, pk=None):
        activity = self.get_object()
        return self._handle_pause(request, activity, auto_resume=False)

    # POST /work-session-activities/{id}/pause-autoresume/
    # Espejo de /pause/: registra la pausa ya resuelta, calculando end_time y
    # resumed_at en el momento de la creación en vez de esperar un /resume/.
    # Payload: { "work_break": <id> }  OR  { "custom_reason": "texto", "work_break_minutes": <int> }
    @action(detail=True, methods=["post"], url_path="pause-autoresume")
    @transaction.atomic
    def pause_autoresume(self, request, pk=None):
        activity = self.get_object()
        return self._handle_pause(request, activity, auto_resume=True)

    # POST /work-session-activities/{id}/resume/
    @action(detail=True, methods=["post"], url_path="resume")
    def resume(self, request, pk=None):
        activity = self.get_object()

        if not activity.is_active:
            return Response({"detail": "La actividad no está activa."}, status=status.HTTP_400_BAD_REQUEST)

        if activity.work_session.is_closed:
            return Response({"detail": "La sesión está cerrada."}, status=status.HTTP_400_BAD_REQUEST)

        active_break = activity.active_break

        if not active_break:
            return Response(
                {"detail": "La actividad no está pausada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()
        active_break.resumed_at = now

        if active_break.work_break_id:
            if not active_break.end_time or active_break.end_time > now:
                active_break.end_time = now
        else:
            active_break.end_time = now

        active_break.save()

        return Response(
            WorkBreakRecordSerializer(active_break).data,
            status=status.HTTP_200_OK,
        )
