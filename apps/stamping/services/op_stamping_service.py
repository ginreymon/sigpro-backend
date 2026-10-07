from apps.stamping.repositories.op_stamping_repository import OPStampingRepository
from apps.production.services.op_production_service import OPProductionService


class OPStampingService:

    @staticmethod
    def get_detalle_estampacion_op_json(tipo_docto, consec_docto):
        stamping_data = OPStampingRepository.get_detalle_estampacion_op_json(tipo_docto, consec_docto)
        if not stamping_data:
            return stamping_data

        # El SP de estampación solo trae header + orderedQty + referenceSams;
        # el resto (colorRows, docStatus, classification, sam, stampingAudit,
        # tracking...) ya lo calcula op_production_service, así que se reusa
        # ese servicio (mismo que usa production-orders/detail) en vez de
        # duplicar esa lógica en un segundo SP. Reusar la variante
        # "_with_tracking" (no el repositorio plano) para que este endpoint
        # sea un superset completo de production-orders/detail y las páginas
        # de estampación puedan dejar de llamar a ese último.
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
        return OPStampingRepository.get_trazabilidad_op_json(consec_docto, tipo_docto)

    @staticmethod
    def get_ordenes_produccion_proceso_json(tipo_docto, consec_docto, id_plan="300"):
        data = OPStampingRepository.get_ordenes_produccion_proceso_json(tipo_docto, consec_docto, id_plan)
        if not data:
            return data

        # hasItemId: true si el SP generó al menos un itemId (colorRows[].items[].itemId).
        data["hasItemId"] = any(
            item.get("itemId")
            for color in data.get("colorRows") or []
            for item in color.get("items") or []
        )
        return data
