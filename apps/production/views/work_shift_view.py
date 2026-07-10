from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import WorkShift
from apps.production.serializers import WorkShiftSerializer


class WorkShiftViewSet(AuditModelViewSet):
    queryset = WorkShift.objects.select_related("location", "location__core_module").all()
    serializer_class = WorkShiftSerializer

    search_fields = ["name", "start_time", "end_time", "location__name"]
