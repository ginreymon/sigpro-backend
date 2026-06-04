import json
from django.db import connection
from apps.production.mappers.recursive_mapper import translate_keys


class ProductivityRepository:

    @staticmethod
    def get_base_productivity(start_date, end_date, employee_id=None, module_id=None, shift_id=None):
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC sp_productividad_base %s, %s, %s, %s, %s",
                [start_date, end_date, module_id, shift_id, employee_id],
            )
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            return translate_keys([dict(zip(columns, row)) for row in rows])

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

