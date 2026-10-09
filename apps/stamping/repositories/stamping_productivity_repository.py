from apps.common.repositories.productivity_repository import BaseProductivityRepository


class StampingProductivityRepository(BaseProductivityRepository):
    efficiency_period_sp = "sp_eficiencia_periodo_estampacion"
    module_shift_summary_sp = "sp_resumen_estampacion"
    module_efficiency_sp = "sp_eficiencia_modulos_estampacion"
    shift_summary_sp = "sp_resumen_estampacion_turno"
