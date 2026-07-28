from apps.stamping.repositories.stamping_productivity_repository import StampingProductivityRepository
from core.utils.date_utils import apply_client_offset


class StampingProductivityService:

    @staticmethod
    def get_efficiency_period(start_date, end_date, client_now, module_id=None, shift_id=None):
        corrected_start = apply_client_offset(start_date, client_now)
        corrected_end   = apply_client_offset(end_date,   client_now)
        return StampingProductivityRepository.get_efficiency_period(
            corrected_start, corrected_end, module_id, shift_id
        )
