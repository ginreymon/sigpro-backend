from apps.common.repositories.sp_json import exec_json_procedure


class OPStampingRepository:

    @staticmethod
    def get_detalle_estampacion_op_json(tipo_docto: str, consec_docto: int):
        # Only operationCenters uses KEY_MAP keys (operacion/centro_id/
        # centro_nombre); the rest of the JSON already comes out in camelCase
        # from the SP and passes through unchanged (fallback in translate_keys).
        return exec_json_procedure(
            "sp_detalle_estampacion_op_json", [tipo_docto, consec_docto]
        )

    @staticmethod
    def get_ordenes_produccion_proceso_json(tipo_docto: str, consec_docto: int, id_plan: str = "300"):
        return exec_json_procedure(
            "sp_ordenes_produccion_proceso_json", [tipo_docto, consec_docto, id_plan]
        )

    @staticmethod
    def get_trazabilidad_op_json(consec_docto: int, tipo_docto: str = None):
        # The SP already returns everything in camelCase; translate_keys only
        # applies the tz-aware fallback on Fecha_Creacion -> createdAt.
        return exec_json_procedure(
            "sp_trazabilidad_op_json", [consec_docto, tipo_docto]
        )
