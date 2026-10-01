import json
from datetime import date

from django.db import connection


class OPTotalsRepository:

    @staticmethod
    def get_totales_registrados_por_op_json(
        date_from: date | None = None,
        date_to: date | None = None,
        op_rowid: int | None = None,
    ):
        """Ejecuta sp_totales_registrados_por_op_json y devuelve el JSON ya
        parseado: [{date, work_centers: [{code, work_center_id, ..., detail: [...]}]}].
        Con date_from=None el SP trae todo, en un único grupo con date=None."""
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC sp_totales_registrados_por_op_json %s, %s, %s",
                [date_from, date_to, op_rowid],
            )
            row = cursor.fetchone()

        return json.loads(row[0]) if row and row[0] else []
