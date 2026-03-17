from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import WorkSession
from apps.production.serializers import WorkSessionSerializer


class WorkSessionViewSet(AuditModelViewSet):
    queryset = WorkSession.objects.all()
    serializer_class = WorkSessionSerializer

    filterset_fields = {
        "user": ["exact"],
        "module": ["exact"],
        "is_closed": ["exact"],
        "started_at": ["gte", "lte"],
    }

    # /work-sessions/{id}/close/
    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        session = self.get_object()

        if session.user != request.user:
            return Response({"detail": "Not allowed"}, status=403)

        if session.is_closed:
            return Response({"detail": "Session already closed"}, status=400)

        session.close_session()

        return Response(self.get_serializer(session).data)

    @action(detail=False, methods=["get"])
    def active(self, request):
        session = WorkSession.objects.filter(user=request.user, is_closed=False).first()

        if not session:
            return Response(None)

        return Response(self.get_serializer(session).data)
