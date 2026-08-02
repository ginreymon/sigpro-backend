from apps.stamping.repositories.stamping_productivity_repository import StampingProductivityRepository
from apps.production.models import Module
from core.utils.date_utils import apply_client_offset


class StampingProductivityService:

    @staticmethod
    def _stamping_module_ids() -> set:
        # A module is a stamping machine iff it has a StampingModuleMachine
        # assignment — this is the structural, always-true discriminator,
        # unlike core_module_id (client-supplied, can be missing/racy).
        return set(
            Module.objects.filter(stamping_machine_assignment__isnull=False)
            .values_list("id", flat=True)
        )

    @staticmethod
    def get_efficiency_period(start_date, end_date, client_now, module_id=None, shift_id=None):
        corrected_start = apply_client_offset(start_date, client_now)
        corrected_end   = apply_client_offset(end_date,   client_now)
        return StampingProductivityRepository.get_efficiency_period(
            corrected_start, corrected_end, module_id, shift_id
        )

    @staticmethod
    def get_module_shift_summary(core_module_id: int | None = None) -> list[dict]:
        data = StampingProductivityRepository.get_module_shift_summary()

        stamping_ids = StampingProductivityService._stamping_module_ids()
        data = [row for row in data if row.get("module_id") in stamping_ids]

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
        data = StampingProductivityRepository.get_module_efficiency(start_date, end_date, module_id)
        stamping_ids = StampingProductivityService._stamping_module_ids()
        return [row for row in data if row.get("module_id") in stamping_ids]
