import json
from django.db import connection
from apps.production.mappers.recursive_mapper import translate_keys


class TechnicalSheetRepository:

    @staticmethod
    def get_technical_sheet_json(sheet_id: int):
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC sp_technical_sheet_json %s",
                [sheet_id],
            )

            row = cursor.fetchone()

            if not row or not row[0]:
                return None

            data = json.loads(row[0])

            return translate_keys(data)

    @staticmethod
    def get_referencias() -> list[dict]:
        with connection.cursor() as cursor:
            cursor.execute("EXEC sp_obtener_referencias")

            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            if not rows:
                return []

            return translate_keys([dict(zip(columns, row)) for row in rows])

    @staticmethod
    def get_sku_reference_info(rowid_item: int) -> dict | None:
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC sp_obtener_referencia_info %s",
                [rowid_item],
            )

            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()

            if not row:
                return None

            return translate_keys(dict(zip(columns, row)))
