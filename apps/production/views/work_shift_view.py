from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import WorkShift
from apps.production.serializers import WorkShiftSerializer


class WorkShiftViewSet(AuditModelViewSet):
    queryset = WorkShift.objects.select_related("location", "location__core_module").all()
    serializer_class = WorkShiftSerializer

    search_fields = ["name", "start_time", "end_time", "location__name"]

    def get_queryset(self):
        queryset = super().get_queryset()
        core_module_id = self.request.query_params.get("core_module_id")
        if core_module_id:
            queryset = queryset.filter(location__core_module_id=core_module_id)
        return queryset
