import json
from django.db import connection
from apps.production.mappers.recursive_mapper import translate_keys


class ProductivityRepository:

    @staticmethod
    def get_efficiency_period(start_date, end_date, module_id=None, shift_id=None):
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC sp_eficiencia_periodo %s, %s, %s, %s",
                [start_date, end_date, module_id, shift_id],
            )
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            return translate_keys([dict(zip(columns, row))])[0] if row else {}

    @staticmethod
    def get_module_shift_summary() -> list[dict]:
        with connection.cursor() as cursor:
            cursor.execute("EXEC sp_resumen_modulos_eficiencia_turno")
            rows = cursor.fetchall()
            if not rows:
                return []
            json_str = ''.join(row[0] for row in rows)
            return translate_keys(json.loads(json_str))

    @staticmethod
    def get_module_efficiency(start_date: str, end_date: str, module_id: int | None = None) -> list[dict]:
        with connection.cursor() as cursor:
            cursor.execute("EXEC sp_eficiencia_modulos %s, %s", [start_date, end_date])
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            result = translate_keys([dict(zip(columns, row)) for row in rows])
            if module_id is not None:
                result = [r for r in result if r.get('module_id') == module_id]
            return result

    @staticmethod
    def get_efficiency_report(start_date, end_date, module_id=None, shift_id=None, employee_id=None):
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC sp_reporte_eficiencia_detallada %s, %s, %s, %s, %s",
                [start_date, end_date, module_id, shift_id, employee_id],
            )
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            result = translate_keys([dict(zip(columns, row)) for row in rows])
            for record in result:
                for field in ("breaks", "employees"):
                    if isinstance(record.get(field), str):
                        record[field] = json.loads(record[field])
            return result

    @staticmethod
    def get_shift_summary(start_date, end_date, shift_id, module_id, employee_id=None):
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC sp_resumen_produccion_turno %s, %s, %s, %s, %s",
                [start_date, end_date, shift_id, module_id, employee_id],
            )
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            result = []
            for row in rows:
                record = dict(zip(columns, row))
                if isinstance(record.get("records_detail"), str):
                    record["records_detail"] = json.loads(record["records_detail"])
                result.append(record)
            return result

