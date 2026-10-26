from apps.common.services.productivity_service import BaseProductivityService
from apps.production.repositories.productivity_repository import ProductivityRepository
from apps.production.models import Module


class ProductivityService(BaseProductivityService):
    repository = ProductivityRepository
    module_model = Module
    is_stamping = False

    @staticmethod
    def get_efficiency_report(start_date: str, end_date: str, module_id=None, shift_id=None, employee_id=None, core_module_id=None):
        data = ProductivityRepository.get_efficiency_report(start_date, end_date, module_id, shift_id, employee_id)

        if core_module_id is None:
            return data

        core_module_by_id = dict(
            Module.objects.values_list("id", "location__core_module_id")
        )
        return [row for row in data if core_module_by_id.get(row.get("module_id")) == core_module_id]
