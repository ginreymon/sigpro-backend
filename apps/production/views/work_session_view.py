from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import WorkSession
from apps.production.serializers import WorkSessionSerializer


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
            WorkSession.objects.filter(user=self.request.user)
            .select_related(
                "work_shift",
                "user",
            )
            .prefetch_related(
                "work_session_activities__module",
                "work_session_activities__employee_snapshots__employee",
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

    @action(detail=False, methods=["get"])
    def active(self, request):
        session = self.get_queryset().filter(is_closed=False).first()

        if not session:
            return Response(None)

        return Response(self.get_serializer(session).data)
