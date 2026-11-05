from apps.common.views.productivity_view import BaseProductivityViewSet
from apps.production.services.productivity_service import ProductivityService
from apps.production.exports.efficiency_report_export import build_efficiency_report_excel


class ProductivityViewSet(BaseProductivityViewSet):
    service = ProductivityService
    efficiency_report_export_builder = staticmethod(build_efficiency_report_excel)
