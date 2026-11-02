from rest_framework import serializers as drf_serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import WorkSession
from apps.production.repositories.work_session_repository import WorkSessionRepository
from apps.production.serializers import WorkSessionSerializer
from apps.production.serializers.work_session_activity_serializer import WorkSessionActivitySerializer
from apps.production.services import work_session_service
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

    # /work-sessions/close-active/
    @action(detail=False, methods=["post"], url_path="close-active")
    def close_active(self, request):
        session = work_session_service.close_active_session(request.user)
        return Response(self.get_serializer(session).data if session else None)

    # /work-sessions/last/
    @action(detail=False, methods=["get"])
    def last(self, request):
        session = work_session_service.get_last_session(request.user)
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
