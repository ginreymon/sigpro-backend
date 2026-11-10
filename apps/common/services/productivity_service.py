from core.utils.date_utils import apply_client_offset


class BaseProductivityService:
    """
    Productivity logic shared by production and stamping. Subclasses set the
    repository, the Module model (`common` must not import `production`) and
    whether they serve stamping machines.
    """

    repository = None
    module_model = None
    area_model = None  # ProductionArea; set by subclasses (`common` must not import `production`)
    is_stamping: bool = False

    @classmethod
    def module_ids(cls) -> set:
        # A module is a stamping machine iff it has a StampingModuleMachine
        # assignment — this is the structural, always-true discriminator,
        # unlike core_module_id (client-supplied, can be missing/racy).
        return set(
            cls.module_model.objects.filter(stamping_machine_assignment__isnull=not cls.is_stamping)
            .values_list("id", flat=True)
        )

    @classmethod
    def get_efficiency_period(cls, start_date, end_date, client_now, module_id=None, shift_id=None):
        corrected_start = apply_client_offset(start_date, client_now)
        corrected_end   = apply_client_offset(end_date,   client_now)
        return cls.repository.get_efficiency_period(
            corrected_start, corrected_end, module_id, shift_id
        )

    @classmethod
    def get_module_shift_summary(cls, core_module_id: int | None = None) -> list[dict]:
        data = cls.repository.get_module_shift_summary()

        module_ids = cls.module_ids()
        data = [row for row in data if row.get("module_id") in module_ids]

        core_module_by_id = dict(
            cls.module_model.objects.values_list("id", "location__core_module_id")
        )
        for row in data:
            row["core_module_id"] = core_module_by_id.get(row.get("module_id"))

        if core_module_id is None:
            return data

        return [row for row in data if row["core_module_id"] == core_module_id]

    @classmethod
    def get_module_efficiency(cls, start_date: str, end_date: str, module_id: int | None = None) -> list[dict]:
        data = cls.repository.get_module_efficiency(start_date, end_date, module_id)
        module_ids = cls.module_ids()
        return [row for row in data if row.get("module_id") in module_ids]

    @classmethod
    def get_balance_summary(cls, start_date, end_date, client_now, module_id=None):
        corrected_start = apply_client_offset(start_date, client_now)
        corrected_end   = apply_client_offset(end_date,   client_now)
        return cls.repository.get_balance_summary(corrected_start, corrected_end, module_id)

    @classmethod
    def get_shift_summary(cls, start_date, end_date, client_now, *, module_id, shift_id, employee_id=None):
        corrected_start = apply_client_offset(start_date, client_now)
        corrected_end   = apply_client_offset(end_date,   client_now)
        return cls.repository.get_shift_summary(
            corrected_start, corrected_end,
            module_id=module_id, shift_id=shift_id, employee_id=employee_id,
        )

    @classmethod
    def get_efficiency_report(cls, start_date: str, end_date: str, module_id=None, shift_id=None, employee_id=None, core_module_id=None):
        data = cls.repository.get_efficiency_report(start_date, end_date, module_id, shift_id, employee_id)
        return cls._filter_by_module(data, "module_id", core_module_id)

    @classmethod
    def get_records_report(cls, start_date: str, end_date: str, module_id=None, shift_id=None, employee_id=None, core_module_id=None):
        data = cls.repository.get_records_report(start_date, end_date, module_id, shift_id, employee_id)
        return cls._filter_by_module(data, "id_modulo", core_module_id)

    @classmethod
    def _filter_by_module(cls, data: list[dict], module_key: str, core_module_id=None) -> list[dict]:
        """Same module scoping for every report: stamping machines only (when stamping) and optional core module."""
        if cls.is_stamping:
            # fn_asignacion_modulos spans every module: keep only stamping machines
            # regardless of the (client-supplied, optional) core_module_id.
            stamping_module_ids = cls.module_ids()
            data = [row for row in data if row.get(module_key) in stamping_module_ids]

        if core_module_id is None:
            return data

        core_module_by_id = dict(
            cls.module_model.objects.values_list("id", "location__core_module_id")
        )
        return [row for row in data if core_module_by_id.get(row.get(module_key)) == core_module_id]

    @classmethod
    def get_area_name(cls, core_module_id: int | None) -> str | None:
        if core_module_id is None:
            return None
        return cls.area_model.objects.filter(core_module_id=core_module_id).values_list("name", flat=True).first()
