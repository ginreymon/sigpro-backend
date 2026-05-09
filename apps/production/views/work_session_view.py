from rest_framework import serializers as drf_serializers
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import WorkSession
from apps.production.serializers import WorkSessionSerializer
from apps.production.serializers.work_session_activity_serializer import WorkSessionActivitySerializer


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
            )
        )

    def perform_create(self, serializer):
        user = self.request.user

        if WorkSession.objects.filter(user=user, is_closed=False).exists():
            raise ValidationError("User already has an active session")

        serializer.save(user=user, created_by=user, updated_by=user)

    # /work-sessions/{id}/close/
    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        session = self.get_queryset().get(pk=pk)

        if session.is_closed:
            return Response({"detail": "Session already closed"}, status=400)

        session.close_session()

        return Response(self.get_serializer(session).data)

    # /work-sessions/active/
    @action(detail=False, methods=["get"])
    def active(self, request):
        session = self.get_queryset().filter(is_closed=False).first()

        if not session:
            return Response(None)

        return Response(self.get_serializer(session).data)

    # /work-sessions/{id}/continue/
    # Crea nueva activity con el mismo módulo de la activity anterior.
    # Usar cuando cambia SKU, empleados, o OP pero el módulo no cambia.
    @action(detail=True, methods=["post"], url_path="continue")
    def continue_activity(self, request, pk=None):
        session = self.get_queryset().get(pk=pk)

        if session.is_closed:
            return Response({"detail": "Session is closed"}, status=400)

        class ContinueInputSerializer(drf_serializers.Serializer):
            employee_ids = drf_serializers.ListField(
                child=drf_serializers.IntegerField(), required=False, allow_empty=True
            )

        input_serializer = ContinueInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        employee_ids = input_serializer.validated_data.get("employee_ids", None)

        new_activity = session.continue_activity(
            employee_ids=employee_ids,
            created_by=request.user,
        )

        return Response(
            WorkSessionActivitySerializer(new_activity, context={"request": request}).data,
            status=201,
        )
