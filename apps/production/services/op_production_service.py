from apps.production.repositories.op_production_repository import OPProductionRepository


class OPProductionService:

    @staticmethod
    def get_detalle_produccion_op(tipo_docto, consec_docto):
        return OPProductionRepository.get_detalle_produccion_op(
            tipo_docto, consec_docto
        )

    @staticmethod
    def get_detalle_componentes_op(tipo_docto, consec_docto, id_plan="300"):
        return OPProductionRepository.get_detalle_componentes_op(
            tipo_docto, consec_docto, id_plan
        )
