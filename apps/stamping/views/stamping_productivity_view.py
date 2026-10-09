from apps.common.views.productivity_view import BaseProductivityViewSet
from apps.stamping.services.stamping_productivity_service import StampingProductivityService


class StampingProductivityViewSet(BaseProductivityViewSet):
    service = StampingProductivityService
