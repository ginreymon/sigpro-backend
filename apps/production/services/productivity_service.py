from django.utils import timezone
from apps.production.repositories.productivity_repository import ProductivityRepository


class ProductivityService:

    @staticmethod
    def _apply_offset(naive_dt, client_now):
        """Shift a naive datetime from client clock to server clock."""
        offset = timezone.now() - client_now
        return naive_dt + offset
    
    @staticmethod
    def get_base_productivity(start_date, end_date, client_now, employee_id=None, module_id=None, shift_id=None):
        corrected_start = ProductivityService._apply_offset(start_date, client_now)
        corrected_end = ProductivityService._apply_offset(end_date, client_now)
        return ProductivityRepository.get_base_productivity(
            corrected_start, corrected_end, employee_id, module_id, shift_id
        )

    @staticmethod
    def get_efficiency_period(start_date, end_date, client_now, employee_id=None, module_id=None, shift_id=None):
        corrected_start = ProductivityService._apply_offset(start_date, client_now)
        corrected_end   = ProductivityService._apply_offset(end_date, client_now)
        return ProductivityRepository.get_efficiency_period(
            corrected_start, corrected_end, employee_id, module_id, shift_id
        )  
