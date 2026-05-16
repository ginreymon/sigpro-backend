from django.db import connection
from apps.production.mappers.recursive_mapper import translate_keys


class ProductivityRepository:

    @staticmethod
    def get_productivity_summary(start_date, end_date, module_id=None, shift_id=None):
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC sp_productividad_resumen %s, %s, %s, %s",
                [start_date, end_date, module_id, shift_id],
            )
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            return translate_keys([dict(zip(columns, row)) for row in rows])

    @staticmethod
    def get_employee_productivity(start_date, end_date, employee_id, module_id=None, shift_id=None):
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC sp_productividad_empleado %s, %s, %s, %s, %s",
                [start_date, end_date, employee_id, module_id, shift_id],
            )
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            return translate_keys([dict(zip(columns, row)) for row in rows])
