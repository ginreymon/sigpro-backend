from apps.common.services.productivity_service import BaseProductivityService
from apps.production.models import Module, ProductionArea
from apps.stamping.repositories.stamping_productivity_repository import StampingProductivityRepository


class StampingProductivityService(BaseProductivityService):
    repository = StampingProductivityRepository
    module_model = Module
    area_model = ProductionArea
    is_stamping = True
