from apps.stamping.repositories.op_stamping_repository import OPStampingRepository
from apps.production.repositories.op_production_repository import OPProductionRepository


class OPStampingService:

    @staticmethod
    def get_detalle_estampacion_op_json(tipo_docto, consec_docto):
        stamping_data = OPStampingRepository.get_detalle_estampacion_op_json(tipo_docto, consec_docto)
        if not stamping_data:
            return stamping_data

        # El SP de estampación solo trae header + orderedQty + referenceSams;
        # el resto (colorRows, docStatus, classification, sam, planId...) ya
        # lo calcula sp_detalle_produccion_op_json, así que se reusa ese
        # repositorio en vez de duplicar esa lógica en un segundo SP.
        production_data = OPProductionRepository.get_detalle_produccion_op_json(tipo_docto, consec_docto) or {}

        return {
            **production_data,
            "orderedQty": stamping_data.get("orderedQty"),
            "referenceSams": stamping_data.get("referenceSams", []),
        }

    @staticmethod
    def get_trazabilidad_op_json(consec_docto, tipo_docto=None):
        return OPStampingRepository.get_trazabilidad_op_json(consec_docto, tipo_docto)
