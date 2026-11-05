from apps.common.views.productivity_view import BaseProductivityViewSet
from apps.production.exports.efficiency_report_export import build_efficiency_report_excel
from apps.stamping.services.stamping_productivity_service import StampingProductivityService


class StampingProductivityViewSet(BaseProductivityViewSet):
    service = StampingProductivityService
    # Same columns as the production report: fn_eficiencia_detallada_estampacion mirrors fn_eficiencia_detallada.
    efficiency_report_export_builder = staticmethod(build_efficiency_report_excel)
