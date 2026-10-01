from datetime import date

from apps.integration.repositories.op_totals_repository import OPTotalsRepository

DETAIL_KEY = "detail"
WORK_CENTERS_KEY = "work_centers"


class OPTotalsService:

    @staticmethod
    def get_totales_registrados_por_op(
        date_from: date | None = None,
        date_to: date | None = None,
        op_rowid: int | None = None,
    ):
        """Una fila por cada item de `work_centers` de sp_totales_registrados_por_op_json,
        con `date` y las columnas del grupo (code, work_center_id, origin, first_start,
        last_end, ...), `detail_count` (largo del array `detail`) y el propio `detail`.
        Ordenadas por fecha, de la más reciente a la más antigua; el `detail` de
        cada grupo, por tipo y número de OP. `id` es
        secuencial dentro de la respuesta: no es una entidad, solo la llave
        de fila que espera la tabla."""
        groups_by_day = OPTotalsRepository.get_totales_registrados_por_op_json(
            date_from, date_to, op_rowid
        )

        # Siempre del día más reciente al más antiguo (AAAA-MM-DD ordena como
        # texto); el grupo sin fecha (consulta sin rango) queda al final.
        groups_by_day = sorted(groups_by_day, key=lambda day: day["date"] or "", reverse=True)

        rows = []
        for day in groups_by_day:
            for group in day[WORK_CENTERS_KEY]:
                detail = sorted(group[DETAIL_KEY], key=lambda item: (item["op_type"], item["op_number"]))
                rows.append({
                    "id": len(rows) + 1,
                    "date": day["date"],
                    **{**group, DETAIL_KEY: detail},
                    "detail_count": len(detail),
                })
        return rows
