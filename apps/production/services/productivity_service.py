from apps.common.services.productivity_service import BaseProductivityService
from apps.production.repositories.productivity_repository import ProductivityRepository
from apps.production.models import Module, ProductionArea


class ProductivityService(BaseProductivityService):
    repository = ProductivityRepository
    module_model = Module
    area_model = ProductionArea
    is_stamping = False
