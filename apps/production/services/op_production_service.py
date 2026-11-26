from apps.production.repositories.op_production_repository import OPProductionRepository
from apps.production.models.production_record import ProductionRecord
from apps.production.models.sku_item_local import SkuItemLocal
from apps.production.models.reference_sam import ReferenceSam
from apps.common.repositories.op_common_repository import OPCommonRepository

CUT_WORK_CENTER_CODE = "CR001"


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
        return OPProductionRepository.get_detalle_produccion_op_json(tipo_docto, consec_docto, id_plan)

    @staticmethod
    def get_detalle_produccion_op_json_with_tracking(tipo_docto, consec_docto, id_plan="300"):
        data = OPProductionService.get_detalle_produccion_op_json(tipo_docto, consec_docto, id_plan)
        if not data:
            return data

        traz_list = OPCommonRepository.get_trazabilidad_op_json(consec_docto, tipo_docto) or []
        op_traz = next(
            (
                t for t in traz_list
                if t.get("documentType") == tipo_docto and t.get("documentNumber") == consec_docto
            ),
            traz_list[0] if traz_list else None,
        )
        if not op_traz:
            return data

        data["stampingAudit"] = op_traz.get("stampingAudit")

        cut_tracking = [
            entry for entry in (op_traz.get("tracking") or [])
            if entry.get("workCenterCode") == CUT_WORK_CENTER_CODE
        ]
        if cut_tracking:
            data["tracking"] = cut_tracking

        return data

    @staticmethod
    def get_cut_tracking(tipo_docto, consec_docto):
        """Cut (CR001) progress of an OP from fn_trazabilidad_op, or None when the
        OP is not in a valid state or has no CR001 operation (never "incomplete")."""
        traz_list = OPCommonRepository.get_trazabilidad_op_json(consec_docto, tipo_docto) or []
        op_traz = next(
            (
                t for t in traz_list
                if t.get("documentType") == tipo_docto and t.get("documentNumber") == consec_docto
            ),
            None,
        )
        if not op_traz:
            return None
        # shortcut: first CR001 entry; if a route repeats CR001, Seg_* is identical per centre.
        return next(
            (e for e in (op_traz.get("tracking") or []) if e.get("workCenterCode") == CUT_WORK_CENTER_CODE),
            None,
        )

    @staticmethod
    def get_sku_detail(tipo_docto, consec_docto, id_plan, sku_rowid):
        data = OPProductionRepository.get_detalle_produccion_op_json(tipo_docto, consec_docto, id_plan)
        if not data:
            return None

        op_rowid = data.get("rowId")

        for color in data.get("colorRows", []):
            for size in color.get("skus", []):
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
