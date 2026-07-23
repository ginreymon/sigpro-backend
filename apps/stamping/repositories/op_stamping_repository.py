from django.db import connection
from apps.production.mappers.recursive_mapper import translate_keys
import json


class OPStampingRepository:

    @staticmethod
    def get_detalle_estampacion_op_json(tipo_docto: str, consec_docto: int):
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC sp_detalle_estampacion_op_json %s, %s",
                [tipo_docto, consec_docto],
            )

            row = cursor.fetchone()

            if not row or not row[0]:
                return None

            # Solo operationCenters usa keys del KEY_MAP (operacion/centro_id/
            # centro_nombre); el resto del JSON ya sale en camelCase desde el
            # SP y pasa sin cambios (fallback en translate_keys).
            return translate_keys(json.loads(row[0]))
