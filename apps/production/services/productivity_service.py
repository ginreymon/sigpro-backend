from apps.common.services.productivity_service import BaseProductivityService
from apps.production.repositories.productivity_repository import ProductivityRepository
from apps.production.models import Module


class ProductivityService(BaseProductivityService):
    repository = ProductivityRepository
    module_model = Module
    is_stamping = False
