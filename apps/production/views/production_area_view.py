from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import ProductionArea
from apps.production.serializers import ProductionAreaSerializer


class ProductionAreaViewSet(AuditModelViewSet):
    queryset = ProductionArea.objects.select_related("core_module").all()
    serializer_class = ProductionAreaSerializer

    search_fields = ["name", "description", "core_module__name"]
