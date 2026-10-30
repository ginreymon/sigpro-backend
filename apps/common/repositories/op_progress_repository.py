import json

from django.db import connection

from apps.common.mappers.recursive_mapper import translate_keys


class OpProgressRepository:
    """Stored-procedure call for the OP progress dashboard widget."""

    op_progress_sp = "dbo.sp_avance_op_modulo_json"

    @classmethod
    def get_op_progress(cls, start_date: str, end_date: str, area_id: int | None = None) -> list[dict]:
        with connection.cursor() as cursor:
            cursor.execute(f"EXEC {cls.op_progress_sp} %s, %s, %s", [start_date, end_date, area_id])
            rows = cursor.fetchall()

        # SQL Server splits long FOR JSON output across several rows: join them all.
        json_str = "".join(row[0] for row in rows if row and row[0])
        if not json_str:
            return []
        # Keys are already snake_case; none of them are in KEY_MAP, so they pass through unchanged.
        return translate_keys(json.loads(json_str))
