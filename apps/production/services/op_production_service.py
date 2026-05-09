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

    @staticmethod
    def get_tipo_documentos_op():
        return OPProductionRepository.get_tipo_documentos_op()

    @staticmethod
    def get_detalle_produccion_op_json(tipo_docto, consec_docto, id_plan="300"):
        return OPProductionRepository.get_detalle_produccion_op_json(tipo_docto, consec_docto, id_plan)

    @staticmethod
    def get_sku_detail(tipo_docto, consec_docto, id_plan, sku_rowid):
        data = OPProductionRepository.get_detalle_produccion_op_json(tipo_docto, consec_docto, id_plan)
        if not data:
            return None

        for color in data.get("colors", []):
            for size in color.get("sizes", []):
                if size.get("skuRowId") == sku_rowid:
                    return {
                        "opRowId": data.get("rowId"),
                        "opType": data.get("documentType"),
                        "opNumber": data.get("documentNumber"),
                        "reference": data.get("reference"),
                        "description": data.get("description"),
                        "color": color.get("color"),
                        "size": size.get("size"),
                        "skuRowId": size.get("skuRowId"),
                        "orderedQty": size.get("orderedQty"),
                        "plannedQty": size.get("plannedQty"),
                        "completedQty": size.get("completedQty"),
                        "wasteQty": size.get("wasteQty"),
                        "rejectedQty": size.get("rejectedQty"),
                        "baseRouteQuantity": size.get("baseRouteQuantity"),
                        "hasOpenRecords": size.get("hasOpenRecords", False),
                    }
        return None
