from apps.production.repositories.op_production_repository import OPProductionRepository
from apps.production.models.production_record import ProductionRecord
from django.db.models import Sum


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

        op_rowid = data.get("rowId")

        for color in data.get("colors", []):
            for size in color.get("sizes", []):
                if size.get("skuRowId") == sku_rowid:

                    records = ProductionRecord.objects.filter(
                        sku_rowid=sku_rowid,
                        op_rowid=op_rowid,
                        op_number=consec_docto,
                        op_type=tipo_docto,
                    )

                    agg = records.aggregate(
                        completedQty=Sum("completed_quantity"),
                        wasteQty=Sum("scrap_quantity"),
                        rejectedQty=Sum("rejected_quantity"),
                    )

                    return {
                        "opRowId": op_rowid,
                        "opType": data.get("documentType"),
                        "opNumber": data.get("documentNumber"),
                        "reference": data.get("reference"),
                        "description": data.get("description"),
                        "color": color.get("color"),
                        "size": size.get("size"),
                        "skuRowId": size.get("skuRowId"),
                        "orderedQty": size.get("orderedQty"),
                        "plannedQty": size.get("plannedQty"),
                        "completedQty": agg["completedQty"] or 0,
                        "wasteQty": agg["wasteQty"] or 0,
                        "rejectedQty": agg["rejectedQty"] or 0,
                        "baseRouteQuantity": size.get("baseRouteQuantity"),
                        "hasOpenRecords": records.filter(end_time__isnull=True).exists(),
                    }
        return None
