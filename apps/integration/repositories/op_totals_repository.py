from django.db import connection


class OPTotalsRepository:

    @staticmethod
    def get_totales_registrados_por_op(op_rowid: int | None = None):
        with connection.cursor() as cursor:
            cursor.execute("EXEC sp_totales_registrados_por_op %s", [op_rowid])

            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            return [dict(zip(columns, row)) for row in rows]
