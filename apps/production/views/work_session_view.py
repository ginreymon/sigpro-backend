from rest_framework import serializers as drf_serializers
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import Module, WorkSession
from apps.production.serializers import WorkSessionSerializer
from apps.production.serializers.work_session_activity_serializer import WorkSessionActivitySerializer
from apps.production.services.employee_assignment_service import validate_employee_conflicts, validate_employees_active, sync_module_assignees
from apps.production.services.work_session_service import (
    force_close,
    get_grace_hours,
    session_core_module_id,
    session_expires_at,
)


class ContinueInputSerializer(drf_serializers.Serializer):
    employee_ids = drf_serializers.ListField(
        child=drf_serializers.IntegerField(), required=False, allow_empty=True
    )
    apprentice_ids = drf_serializers.ListField(
        child=drf_serializers.IntegerField(), required=False, allow_empty=True
    )


class WorkSessionViewSet(AuditModelViewSet):
    queryset = WorkSession.objects.all()
    serializer_class = WorkSessionSerializer

    filterset_fields = {
        "user": ["exact"],
        "is_closed": ["exact"],
        "started_at": ["gte", "lte"],
    }

    def get_queryset(self):
        return (
            WorkSession.objects.all()
            .select_related(
                "work_shift",
                "user",
            )
            .prefetch_related(
                "work_session_activities__module",
                "work_session_activities__employee_snapshots__employee",
                "work_session_activities__work_break_records",
                "work_session_activities__production_records",
            )
        )

    def perform_create(self, serializer):
        user = self.request.user

        with transaction.atomic():
            active = (
                WorkSession.objects.select_for_update()
                .filter(user=user, is_closed=False)
                .first()
            )
            if active:
                target_module_id = self.request.data.get("module_id")
                if target_module_id:
                    target_module = (
                        Module.objects.select_related("location")
                        .filter(id=target_module_id)
                        .first()
                    )
                    target_core_module_id = (
                        target_module.location.core_module_id
                        if target_module and target_module.location_id
                        else None
                    )
                    if str(session_core_module_id(active)) != str(target_core_module_id):
                        raise ValidationError(
                            "Ya tienes una sesión activa en otro proceso. Ciérrala antes de iniciar una nueva."
                        )
                active.close_session()
            serializer.save(user=user, created_by=user, updated_by=user)

    # /work-sessions/{id}/close/
    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        session = self.get_object()

        if session.is_closed:
            return Response({"detail": "Session already closed"}, status=400)

        session.close_session()

        session = self.get_queryset().get(pk=pk)
        return Response(self.get_serializer(session).data)

    # /work-sessions/active/
    @action(detail=False, methods=["get"])
    def active(self, request):
        session = self.get_queryset().filter(is_closed=False, user=request.user).first()

        if not session:
            return Response(None)

        core_module_id = request.query_params.get("core_module_id")
        if core_module_id and str(session_core_module_id(session)) != str(core_module_id):
            return Response(None)

        grace_hours = get_grace_hours()
        expires_at = session_expires_at(session, grace_hours)

        if timezone.now() >= expires_at:
            force_close(session, expires_at)
            return Response(None)

        return Response(self.get_serializer(session).data)

    # /work-sessions/{id}/rotate/
    # Cierra activity actual y abre una nueva con el mismo módulo.
    # Usar cuando cambia SKU, empleados, o OP pero el módulo no cambia.
    @action(detail=True, methods=["post"], url_path="rotate")
    @transaction.atomic
    def rotate_activity(self, request, pk=None):
        session = WorkSession.objects.select_for_update().select_related("work_shift").get(pk=pk)

        if session.is_closed:
            return Response({"detail": "La sesión está cerrada."}, status=400)

        grace_hours = get_grace_hours()
        expires_at = session_expires_at(session, grace_hours)

        if timezone.now() >= expires_at:
            force_close(session, expires_at)
            return Response(["La sesión ha expirado."], status=400)

        input_serializer = ContinueInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        employee_ids = input_serializer.validated_data.get("employee_ids", None)
        apprentice_ids = input_serializer.validated_data.get("apprentice_ids", None)

        current_activity = session.get_active_activity()

        if employee_ids is not None:
            resolved_employee_ids = employee_ids
        elif current_activity:
            resolved_employee_ids = list(
                current_activity.employee_snapshots.values_list("employee_id", flat=True)
            )
        else:
            resolved_employee_ids = []

        validate_employees_active(resolved_employee_ids)
        validate_employee_conflicts(resolved_employee_ids, current_activity)

        try:
            new_activity = session.restart_activity(
                employee_ids=employee_ids,
                created_by=request.user,
                apprentice_ids=apprentice_ids,
            )
        except LookupError as e:
            return Response({"detail": str(e)}, status=400)

        sync_module_assignees(new_activity.module, request.user)

        return Response(
            WorkSessionActivitySerializer(new_activity, context={"request": request}).data,
            status=201,
        )
