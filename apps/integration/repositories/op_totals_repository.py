import json
from datetime import date, datetime

from django.db import connection


class OPTotalsRepository:

    @staticmethod
    def get_totales_registrados_por_op_json(
        date_from: date | None = None,
        date_to: date | None = None,
        op_rowid: int | None = None,
    ):
        """Ejecuta sp_totales_registrados_por_op_json y devuelve el JSON ya
        parseado: [{day_number, record_date, code, work_center_id, ..., detail: [...]}].
        Con date_from=None el SP trae todo, con day_number y record_date en None."""
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC sp_totales_registrados_por_op_json %s, %s, %s",
                [date_from, date_to, op_rowid],
            )
            row = cursor.fetchone()

        return json.loads(row[0]) if row and row[0] else []

    @staticmethod
    def get_totales_por_work_center_json(
        op_rowid: int | None = None,
        first_start_from: datetime | None = None,
        last_end_to: datetime | None = None,
    ):
        """Runs sp_totales_registrados_por_op_work_center_json and returns the parsed
        JSON: [{code, work_center_id, ..., documents: [...]}] (no day split)."""
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC sp_totales_registrados_por_op_work_center_json %s, %s, %s",
                [op_rowid, first_start_from, last_end_to],
            )
            row = cursor.fetchone()

        return json.loads(row[0]) if row and row[0] else []
