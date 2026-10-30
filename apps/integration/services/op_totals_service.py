from datetime import date, datetime

from apps.common.mappers.recursive_mapper import translate_keys
from apps.integration.repositories.op_totals_repository import OPTotalsRepository

DETAIL_KEY = "detail"
DOCUMENTS_KEY = "documents"

STATUS_PENDING = "PENDING"
STATUS_MISSING = "MISSING"
STATUS_INTEGRATED = "INTEGRATED"
INTEGRATION_STATUSES = (STATUS_PENDING, STATUS_MISSING, STATUS_INTEGRATED)


class OPTotalsService:

    @staticmethod
    def get_totales_registrados_por_op(
        date_from: date | None = None,
        date_to: date | None = None,
        op_rowid: int | None = None,
    ):
        """Una fila por cada item del arreglo de sp_totales_registrados_por_op_json,
        con las columnas del grupo (day_number, record_date, code, work_center_id, origin,
        first_start, last_end, ...), `detail_count` (largo del array `detail`) y el propio `detail`.
        Ordenadas por fecha, de la más reciente a la más antigua; el `detail` de
        cada grupo, por tipo y número de OP. `id` es
        secuencial dentro de la respuesta: no es una entidad, solo la llave
        de fila que espera la tabla."""
        groups = OPTotalsRepository.get_totales_registrados_por_op_json(
            date_from, date_to, op_rowid
        )

        # Siempre del día más reciente al más antiguo (day_number mayor primero);
        # el grupo sin día (consulta sin rango) queda al final.
        groups = sorted(groups, key=lambda group: group.get("day_number") or 0, reverse=True)

        rows = []
        for group in groups:
            detail = sorted(group[DETAIL_KEY], key=lambda item: (item["op_type"], item["op_number"]))
            rows.append({
                "id": len(rows) + 1,
                **{**group, DETAIL_KEY: detail},
                "detail_count": len(detail),
            })
        return rows

    @staticmethod
    def get_detalle_sku_op(op_type: str, op_number: int) -> dict:
        """Color x size detail of one Confección OP, `{"colorRows": [...]}`, with the keys translated
        like production-orders/detail and by-work-center. Includes SKUs already integrated."""
        color_rows = OPTotalsRepository.get_detalle_integracion_op_produccion_json(op_type, op_number)
        return translate_keys({"ColorRows": color_rows})

    @staticmethod
    def get_estado_integracion(
        op_rowid: int | None = None,
        first_start_from: datetime | None = None,
        last_end_to: datetime | None = None,
        status: str | None = None,
    ):
        """One row per OP / origin / work center with its integrated, pending and
        missing quantities and `integration_status`, optionally filtered by status.
        Sorted by OP type and number; `id` is sequential within the response (the
        table's row key, not an entity)."""
        rows = OPTotalsRepository.get_estado_integracion(op_rowid, first_start_from, last_end_to)

        if status:
            rows = [row for row in rows if row["integration_status"] == status]

        rows.sort(key=lambda row: (row["op_type"], row["op_number"], row["code"] or ""))
        return [{"id": index + 1, **row} for index, row in enumerate(rows)]

    @staticmethod
    def get_resumen_integracion(
        op_rowid: int | None = None,
        first_start_from: datetime | None = None,
        last_end_to: datetime | None = None,
    ):
        """Counters for the integration dashboard: rows (OP / work center) and
        quantities per status, over the same filters as get_estado_integracion."""
        rows = OPTotalsRepository.get_estado_integracion(op_rowid, first_start_from, last_end_to)

        summary = {
            "total": len(rows),
            "integrated_quantity": sum(row["integrated_quantity"] or 0 for row in rows),
            "pending_quantity": sum(row["pending_quantity"] or 0 for row in rows),
            "missing_quantity": sum(row["missing_quantity"] or 0 for row in rows),
        }
        for status in INTEGRATION_STATUSES:
            summary[status.lower()] = sum(1 for row in rows if row["integration_status"] == status)
        return summary

    @staticmethod
    def get_totales_por_work_center(
        op_rowid: int | None = None,
        first_start_from: datetime | None = None,
        last_end_to: datetime | None = None,
    ):
        """One row per work center of sp_totales_registrados_por_op_work_center_json,
        with `documents_count` and its `documents` sorted by OP type and number. `id` is
        sequential within the response: the table's row key, not an entity."""
        groups = OPTotalsRepository.get_totales_por_work_center_json(
            op_rowid, first_start_from, last_end_to
        )

        rows = []
        for group in groups:
            # `detail` comes straight from the SQL function: {"ColorRows": [...]} (Confección,
            # Spanish keys translated like production-orders/detail does) or {"referenceSams": [...]}
            # (Estampación, already in snake_case; translate_keys leaves it unchanged).
            documents = sorted(
                (
                    {**item, DETAIL_KEY: translate_keys(item.get(DETAIL_KEY))}
                    for item in group[DOCUMENTS_KEY]
                ),
                key=lambda item: (item["op_type"], item["op_number"]),
            )
            rows.append({
                "id": len(rows) + 1,
                **{**group, DOCUMENTS_KEY: documents},
                "documents_count": len(documents),
            })
        return rows
