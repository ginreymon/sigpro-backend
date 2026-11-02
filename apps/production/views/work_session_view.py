from django.db import transaction
from rest_framework import serializers as drf_serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import WorkSession
from apps.production.repositories.work_session_repository import WorkSessionRepository
from apps.production.serializers import WorkSessionSerializer
from apps.production.serializers.work_session_activity_serializer import WorkSessionActivitySerializer
from apps.production.services import work_session_service
from apps.production.services.exceptions import SessionRuleError
from apps.production.views.session_rule_error_mixin import SessionRuleErrorMixin


class ContinueInputSerializer(drf_serializers.Serializer):
    employee_ids = drf_serializers.ListField(
        child=drf_serializers.IntegerField(), required=False, allow_empty=True
    )
    apprentice_ids = drf_serializers.ListField(
        child=drf_serializers.IntegerField(), required=False, allow_empty=True
    )


class WorkSessionViewSet(SessionRuleErrorMixin, AuditModelViewSet):
    """The session rules (single open session per user, expiry, rotation) live
    in work_session_service; this view only reads the request and serializes."""

    queryset = WorkSession.objects.all()
    serializer_class = WorkSessionSerializer

    filterset_fields = {
        "user": ["exact"],
        "is_closed": ["exact"],
        "started_at": ["gte", "lte"],
    }

    def get_queryset(self):
        return WorkSessionRepository.detail_queryset()

    def perform_create(self, serializer):
        user = self.request.user
        work_session_service.open_session(
            user,
            self.request.data.get("module_id"),
            create=lambda: serializer.save(user=user, created_by=user, updated_by=user),
        )

    # /work-sessions/{id}/close/
    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        session = work_session_service.close(self.get_object())
        return Response(self.get_serializer(session).data)

    # /work-sessions/{id}/clone/
    # Closes session {id} if it is still open (same logic as /close/), then runs the
    # POST /work-sessions/ flow with the payload rebuilt from it. One transaction:
    # if the close or the creation fails, nothing is persisted.
    @action(detail=True, methods=["post"])
    def clone(self, request, pk=None):
        original = self.get_object()  # object-level lookup/permissions

        with transaction.atomic():
            session = WorkSessionRepository.lock_by_id(original.pk)
            if not session.is_closed:
                session = work_session_service.close(session)
                if not session.is_closed:
                    raise SessionRuleError({"detail": "No se pudo cerrar la jornada (sesión) original."})

            serializer = self.get_serializer(data=work_session_service.clone_payload(session))
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

        return Response(serializer.data, status=201)

    # /work-sessions/close-active/
    @action(detail=False, methods=["post"], url_path="close-active")
    def close_active(self, request):
        session = work_session_service.close_active_session(request.user)
        return Response(self.get_serializer(session).data if session else None)

    # /work-sessions/last/
    @action(detail=False, methods=["get"])
    def last(self, request):
        # ?close-expired=true closes the session if it is open past shift end + grace.
        close_expired = request.query_params.get("close-expired", "").lower() == "true"
        session = work_session_service.get_last_session(request.user, close_expired)
        return Response(self.get_serializer(session).data if session else None)

    # /work-sessions/active/
    @action(detail=False, methods=["get"])
    def active(self, request):
        session = work_session_service.get_active_session(
            request.user, request.query_params.get("core_module_id")
        )

        if not session:
            return Response(None)

        return Response(self.get_serializer(session).data)

    # /work-sessions/{id}/rotate/
    # Cierra activity actual y abre una nueva con el mismo módulo.
    # Usar cuando cambia SKU, empleados, o OP pero el módulo no cambia.
    @action(detail=True, methods=["post"], url_path="rotate")
    def rotate_activity(self, request, pk=None):
        def read_input():
            input_serializer = ContinueInputSerializer(data=request.data)
            input_serializer.is_valid(raise_exception=True)
            return (
                input_serializer.validated_data.get("employee_ids", None),
                input_serializer.validated_data.get("apprentice_ids", None),
            )

        new_activity = work_session_service.rotate_activity(pk, request.user, read_input)

        return Response(
            WorkSessionActivitySerializer(new_activity, context={"request": request}).data,
            status=201,
        )
