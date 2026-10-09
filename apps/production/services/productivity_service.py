from apps.common.services.productivity_service import BaseProductivityService
from apps.production.repositories.productivity_repository import ProductivityRepository
from apps.production.models import Module
from core.utils.date_utils import apply_client_offset


class ProductivityService(BaseProductivityService):
    repository = ProductivityRepository
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

    @staticmethod
    def get_balance_summary(start_date, end_date, client_now, module_id=None):
        corrected_start = apply_client_offset(start_date, client_now)
        corrected_end   = apply_client_offset(end_date,   client_now)
        return ProductivityRepository.get_balance_summary(corrected_start, corrected_end, module_id)
