from apps.common.repositories.op_common_repository import OPCommonRepository
from apps.stamping.repositories.op_stamping_repository import OPStampingRepository
from apps.production.services.op_production_service import OPProductionService


class OPStampingService:

    @staticmethod
    def get_detalle_estampacion_op_json(tipo_docto, consec_docto):
        stamping_data = OPStampingRepository.get_detalle_estampacion_op_json(tipo_docto, consec_docto)
        if not stamping_data:
            return stamping_data

        # The stamping SP only returns header + orderedQty + referenceSams;
        # the rest (colorRows, docStatus, classification, sam, stampingAudit,
        # tracking...) is already computed by op_production_service, so that
        # service (the one production-orders/detail uses) is reused instead of
        # duplicating that logic in a second SP. The "_with_tracking" variant
        # (not the plain repository) is reused so this endpoint is a complete
        # superset of production-orders/detail and the stamping pages can stop
        # calling the latter.
        production_data = OPProductionService.get_detalle_produccion_op_json_with_tracking(
            tipo_docto, consec_docto
        ) or {}

        return {
            **production_data,
            "orderedQty": stamping_data.get("orderedQty"),
            "referenceSams": stamping_data.get("referenceSams", []),
        }

    @staticmethod
    def get_trazabilidad_op_json(consec_docto, tipo_docto=None):
        return OPCommonRepository.get_trazabilidad_op_json(consec_docto, tipo_docto)

    @staticmethod
    def get_ordenes_produccion_proceso_json(tipo_docto, consec_docto, id_plan="300"):
        data = OPStampingRepository.get_ordenes_produccion_proceso_json(tipo_docto, consec_docto, id_plan)
        if not data:
            return data

        # hasItemId: true if the SP generated at least one itemId (colorRows[].items[].itemId).
        data["hasItemId"] = any(
            item.get("itemId")
            for color in data.get("colorRows") or []
            for item in color.get("items") or []
        )
        return data
