from django.db import connection
from apps.common.mappers.recursive_mapper import translate_keys


class SkuReferenceRepository:

    @staticmethod
    def get_references() -> list[dict]:
        with connection.cursor() as cursor:
            cursor.execute("EXEC sp_obtener_referencias")

            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            return translate_keys([dict(zip(columns, row)) for row in rows])
