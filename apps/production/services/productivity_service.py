from apps.production.repositories.productivity_repository import ProductivityRepository
from core.utils.date_utils import apply_client_offset


class ProductivityService:

    @staticmethod
    def get_base_productivity(start_date, end_date, client_now, employee_id=None, module_id=None, shift_id=None):
        corrected_start = apply_client_offset(start_date, client_now)
        corrected_end   = apply_client_offset(end_date,   client_now)
        return ProductivityRepository.get_base_productivity(
            corrected_start, corrected_end, employee_id, module_id, shift_id
        )

    @staticmethod
    def get_efficiency_period(start_date, end_date, client_now, module_id=None, shift_id=None):
        corrected_start = apply_client_offset(start_date, client_now)
        corrected_end   = apply_client_offset(end_date,   client_now)
        return ProductivityRepository.get_efficiency_period(
            corrected_start, corrected_end, module_id, shift_id
        )

    @staticmethod
    def get_module_shift_summary() -> list[dict]:
        return ProductivityRepository.get_module_shift_summary()

    @staticmethod
    def get_shift_summary(start_date, end_date, client_now, shift_id, module_id, employee_id=None):
        corrected_start = apply_client_offset(start_date, client_now)
        corrected_end   = apply_client_offset(end_date,   client_now)
        return ProductivityRepository.get_shift_summary(
            corrected_start, corrected_end, shift_id, module_id, employee_id
        )
