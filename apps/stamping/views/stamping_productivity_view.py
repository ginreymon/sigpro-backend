from apps.common.views.productivity_view import BaseProductivityViewSet
from apps.stamping.exports.stamping_efficiency_report_export import build_stamping_efficiency_report_excel
from apps.stamping.services.stamping_productivity_service import StampingProductivityService


class StampingProductivityViewSet(BaseProductivityViewSet):
    service = StampingProductivityService
    # Stamping-specific layout (pieces, shift-based productivity); the Confección report keeps the shared builder.
    efficiency_report_export_builder = staticmethod(build_stamping_efficiency_report_excel)
