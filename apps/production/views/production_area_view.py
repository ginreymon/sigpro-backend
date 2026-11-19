from core.views.audit_model_view import AuditModelViewSet
from apps.production.models import ProductionArea
from apps.production.serializers import ProductionAreaSerializer
from core import option_keys as opt


class ProductionAreaViewSet(AuditModelViewSet):
    write_options = (opt.MODULES, opt.GENERAL_CONFIG, opt.SEWING_CONFIG)

    queryset = ProductionArea.objects.select_related("core_module").all()
    serializer_class = ProductionAreaSerializer

    search_fields = ["name", "description", "core_module__name"]
