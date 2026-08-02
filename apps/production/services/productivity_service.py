from apps.production.repositories.productivity_repository import ProductivityRepository
from apps.production.models import Module
from core.utils.date_utils import apply_client_offset


class ProductivityService:

    @staticmethod
    def _production_module_ids() -> set:
        # A module is a stamping machine iff it has a StampingModuleMachine
        # assignment — this is the structural, always-true discriminator,
        # unlike core_module_id (client-supplied, can be missing/racy).
        return set(
            Module.objects.filter(stamping_machine_assignment__isnull=True)
            .values_list("id", flat=True)
        )

    @staticmethod
    def get_efficiency_period(start_date, end_date, client_now, module_id=None, shift_id=None):
        corrected_start = apply_client_offset(start_date, client_now)
        corrected_end   = apply_client_offset(end_date,   client_now)
        return ProductivityRepository.get_efficiency_period(
            corrected_start, corrected_end, module_id, shift_id
        )

    @staticmethod
    def get_module_shift_summary(core_module_id: int | None = None) -> list[dict]:
        data = ProductivityRepository.get_module_shift_summary()

        production_ids = ProductivityService._production_module_ids()
        data = [row for row in data if row.get("module_id") in production_ids]

        core_module_by_id = dict(
            Module.objects.values_list("id", "location__core_module_id")
        )
        for row in data:
            row["core_module_id"] = core_module_by_id.get(row.get("module_id"))

        if core_module_id is None:
            return data

        return [row for row in data if row["core_module_id"] == core_module_id]

    @staticmethod
    def get_module_efficiency(start_date: str, end_date: str, module_id: int | None = None) -> list[dict]:
        data = ProductivityRepository.get_module_efficiency(start_date, end_date, module_id)
        production_ids = ProductivityService._production_module_ids()
        return [row for row in data if row.get("module_id") in production_ids]

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
    def get_shift_summary(start_date, end_date, client_now, shift_id, module_id, employee_id=None):
        corrected_start = apply_client_offset(start_date, client_now)
        corrected_end   = apply_client_offset(end_date,   client_now)
        return ProductivityRepository.get_shift_summary(
            corrected_start, corrected_end, shift_id, module_id, employee_id
        )

    @staticmethod
    def get_balance_summary(start_date, end_date, client_now, module_id=None):
        corrected_start = apply_client_offset(start_date, client_now)
        corrected_end   = apply_client_offset(end_date,   client_now)
        return ProductivityRepository.get_balance_summary(corrected_start, corrected_end, module_id)
