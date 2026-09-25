from apps.integration.repositories.op_totals_repository import OPTotalsRepository


class OPTotalsService:

    @staticmethod
    def get_totales_registrados_por_op(op_rowid: int | None = None):
        return OPTotalsRepository.get_totales_registrados_por_op(op_rowid)
