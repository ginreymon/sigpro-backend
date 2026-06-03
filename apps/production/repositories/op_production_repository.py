from django.db import connection
from apps.production.mappers.recursive_mapper import translate_keys
import json


class OPProductionRepository:

    @staticmethod
    def get_detalle_produccion_op(tipo_docto: str, consec_docto: int):
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC sp_detalle_produccion_op %s, %s", [tipo_docto, consec_docto]
            )

            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            return [dict(zip(columns, row)) for row in rows]

    @staticmethod
    def get_detalle_componentes_op(tipo_docto: str, consec_docto: int, id_plan: str = "300"):
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC sp_detalle_componentes_op %s, %s, %s",
                [tipo_docto, consec_docto, id_plan],
            )

            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            return [dict(zip(columns, row)) for row in rows]

    @staticmethod
    def get_tipo_documentos_op():
        with connection.cursor() as cursor:
            cursor.execute("EXEC sp_tipo_documentos_op", [])

            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            return [dict(zip(columns, row)) for row in rows]

    @staticmethod
    def get_detalle_produccion_op_json(tipo_docto: str, consec_docto: int, id_plan: str = "300"):
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC sp_detalle_produccion_op_json %s, %s, %s",
                [tipo_docto, consec_docto, id_plan],
            )

            row = cursor.fetchone()

            if not row or not row[0]:
                return None
            
            data =json.loads(row[0])

            return translate_keys(data)

    @staticmethod
    def get_materiales_op_json(tipo_docto: str, consec_docto: int):
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC sp_obtener_materiales_op_json %s, %s",
                [tipo_docto, consec_docto],
            )

            row = cursor.fetchone()

            if not row or not row[0]:
                return None

            return translate_keys(json.loads(row[0]))
