from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import WorkSessionActivity
from apps.production.serializers.work_session_activity_serializer import WorkSessionActivitySerializer


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
