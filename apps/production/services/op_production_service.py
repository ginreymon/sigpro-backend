from apps.production.repositories.op_production_repository import OPProductionRepository
from apps.production.models.production_record import ProductionRecord
from apps.production.models.sku_item_local import SkuItemLocal
from apps.production.models.reference_sam import ReferenceSam


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
    def get_materiales_op_json(tipo_docto, consec_docto):
        return OPProductionRepository.get_materiales_op_json(tipo_docto, consec_docto)

    @staticmethod
    def get_detalle_produccion_op_json(tipo_docto, consec_docto, id_plan="300"):
        data = OPProductionRepository.get_detalle_produccion_op_json(tipo_docto, consec_docto, id_plan)
        if data:
            data["statusInfo"] = {"state": data.get("status"), "name": data.pop("statusName", None)}
        return data

    @staticmethod
    def get_sku_detail(tipo_docto, consec_docto, id_plan, sku_rowid):
        data = OPProductionRepository.get_detalle_produccion_op_json(tipo_docto, consec_docto, id_plan)
        if not data:
            return None

        op_rowid = data.get("rowId")

        for color in data.get("colorRows", []):
            for size in color.get("sizes", []):
                if size.get("skuRowId") == sku_rowid:

                    records = ProductionRecord.objects.filter(
                        sku_rowid=sku_rowid,
                        op_number=consec_docto,
                        op_type=tipo_docto,
                    )

                    sku_local = SkuItemLocal.objects.filter(rowid=sku_rowid).values("rowid_item").first()
                    sam_value = None
                    if sku_local:
                        ref_sam = ReferenceSam.objects.filter(rowid_item=sku_local["rowid_item"]).values("sam").first()
                        sam_value = float(ref_sam["sam"]) if ref_sam else None

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
                        "completedQty": size.get("completedQty"),
                        "wasteQty": size.get("wasteQty"),
                        "rejectedQty": size.get("rejectedQty"),
                        "baseRouteQuantity": size.get("baseRouteQuantity"),
                        "hasOpenRecords": records.filter(end_time__isnull=True).exists(),
                        "sam": sam_value,
                    }
        return None
