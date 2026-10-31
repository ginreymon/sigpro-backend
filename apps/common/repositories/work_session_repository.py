import json

from django.db import connection

from apps.common.mappers.recursive_mapper import translate_keys


class WorkSessionRepository:
    """Stored-procedure call for the paginated work session listing."""

    work_sessions_sp = "dbo.sp_sesiones_trabajo_op_json"

    @classmethod
    def list_work_sessions(
        cls,
        start_date: str | None,
        end_date: str | None,
        op_number: int | None,
        op_type: str | None,
        reference: str | None,
        module_name: str | None,
        offset: int,
        limit: int,
    ) -> list[dict]:
        with connection.cursor() as cursor:
            cursor.execute(
                f"EXEC {cls.work_sessions_sp} %s, %s, %s, %s, %s, %s, %s, %s",
                [start_date, end_date, op_number, op_type, reference, module_name, offset, limit],
            )
            rows = cursor.fetchall()

        # SQL Server may split long JSON output across several rows: join them all.
        json_str = "".join(row[0] for row in rows if row and row[0])
        return translate_keys(json.loads(json_str)) if json_str else []
