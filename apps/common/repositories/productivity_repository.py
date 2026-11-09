import json

from django.db import connection

from apps.common.mappers.recursive_mapper import translate_keys


def rows_with_json(cursor, json_field: str) -> list[dict]:
    """
    Fetches every row of the cursor as a dict, decoding `json_field` when the SP
    returns it as JSON text.
    """
    columns = [col[0] for col in cursor.description]
    result = []
    for row in cursor.fetchall():
        record = dict(zip(columns, row))
        if isinstance(record.get(json_field), str):
            record[json_field] = json.loads(record[json_field])
        result.append(record)
    return result


class BaseProductivityRepository:
    """
    Productivity stored-procedure calls shared by production and stamping.
    Subclasses only set the SP names.
    """

    efficiency_period_sp: str
    module_shift_summary_sp: str
    module_efficiency_sp: str
    shift_summary_sp: str
    balance_summary_sp: str
    efficiency_report_sp: str

    @classmethod
    def get_balance_summary(cls, start_date, end_date, module_id=None):
        with connection.cursor() as cursor:
            cursor.execute(
                f"EXEC {cls.balance_summary_sp} %s, %s, %s",
                [start_date, end_date, module_id],
            )
            return rows_with_json(cursor, "records_detail")

    @classmethod
    def get_efficiency_period(cls, start_date, end_date, module_id=None, shift_id=None):
        with connection.cursor() as cursor:
            cursor.execute(
                f"EXEC {cls.efficiency_period_sp} %s, %s, %s, %s",
                [start_date, end_date, module_id, shift_id],
            )
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            return translate_keys([dict(zip(columns, row))])[0] if row else {}

    @classmethod
    def get_efficiency_report(cls, start_date, end_date, module_id=None, shift_id=None, employee_id=None):
        with connection.cursor() as cursor:
            cursor.execute(
                f"EXEC {cls.efficiency_report_sp} %s, %s, %s, %s, %s",
                [start_date, end_date, module_id, shift_id, employee_id],
            )
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            result = translate_keys([dict(zip(columns, row)) for row in rows])
            for record in result:
                for field in ("breaks", "employees", "additional_times", "production_orders"):
                    if isinstance(record.get(field), str):
                        try:
                            record[field] = json.loads(record[field])
                        except ValueError:
                            record[field] = []
            return result

    @classmethod
    def get_module_shift_summary(cls) -> list[dict]:
        with connection.cursor() as cursor:
            cursor.execute(f"EXEC {cls.module_shift_summary_sp}")
            rows = cursor.fetchall()
            if not rows:
                return []
            json_str = ''.join(row[0] for row in rows)
            return translate_keys(json.loads(json_str))

    @classmethod
    def get_module_efficiency(cls, start_date: str, end_date: str, module_id: int | None = None) -> list[dict]:
        with connection.cursor() as cursor:
            cursor.execute(f"EXEC {cls.module_efficiency_sp} %s, %s", [start_date, end_date])
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            result = translate_keys([dict(zip(columns, row)) for row in rows])
            if module_id is not None:
                result = [r for r in result if r.get('module_id') == module_id]
            return result

    @classmethod
    def get_shift_summary(cls, start_date, end_date, *, module_id, shift_id, employee_id=None):
        # Keyword-only ids: the SP expects (module_id, shift_id) and a swapped
        # positional order would fail silently.
        with connection.cursor() as cursor:
            cursor.execute(
                f"EXEC {cls.shift_summary_sp} %s, %s, %s, %s, %s",
                [start_date, end_date, module_id, shift_id, employee_id],
            )
            return rows_with_json(cursor, "records_detail")
