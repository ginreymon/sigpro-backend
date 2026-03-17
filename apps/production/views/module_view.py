from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import Module
from apps.production.serializers import ModuleSerializer


class ModuleViewSet(AuditModelViewSet):
    queryset = Module.objects.select_related("work_center").all()
    serializer_class = ModuleSerializer

    search_fields = [
        "name",
        "number",
        "operator_count",
        "location",
        "work_center__description",
        "work_center__code",
        "work_center__short_description",
    ]
