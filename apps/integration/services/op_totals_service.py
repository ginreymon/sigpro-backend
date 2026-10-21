from datetime import date, datetime

from apps.integration.repositories.op_totals_repository import OPTotalsRepository

DETAIL_KEY = "detail"
DOCUMENTS_KEY = "documents"


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
            documents = sorted(
                group[DOCUMENTS_KEY], key=lambda item: (item["op_type"], item["op_number"])
            )
            rows.append({
                "id": len(rows) + 1,
                **{**group, DOCUMENTS_KEY: documents},
                "documents_count": len(documents),
            })
        return rows
