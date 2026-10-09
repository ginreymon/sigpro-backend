from apps.common.services.productivity_service import BaseProductivityService
from apps.stamping.repositories.stamping_productivity_repository import StampingProductivityRepository


class StampingProductivityService(BaseProductivityService):
    repository = StampingProductivityRepository
    is_stamping = True
