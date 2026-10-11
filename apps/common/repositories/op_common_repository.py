from apps.common.repositories.sp_json import exec_json_procedure


class OPCommonRepository:
    """Order (OP) lookups backed by stored procedures in database/sp/common,
    shared by production and stamping."""

    @staticmethod
    def get_trazabilidad_op_json(consec_docto: int, tipo_docto: str = None):
        # The SP already returns everything in camelCase; translate_keys only
        # applies the tz-aware fallback on Fecha_Creacion -> createdAt.
        return exec_json_procedure(
            "sp_trazabilidad_op_json", [consec_docto, tipo_docto]
        )
