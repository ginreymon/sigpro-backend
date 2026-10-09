import json
from django.db import connection
from apps.common.mappers.recursive_mapper import translate_keys


def _to_float(value):
    return float(value) if value is not None else None


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
                [start_date, end_date, module_id, shift_id, employee_id],
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

    @staticmethod
    def get_tiempos_operacion_modulo(fecha_inicio, module_id, shift_id, tipo_modulo='production'):
        """
        EXEC sp_tiempos_operacion_modulo — solo se necesitan los indicadores
        (result set 2); el detalle (result set 1) se descarta.

        fecha_inicio debe ser el inicio de turno ya convertido a UTC naive
        (ver apps.production.services.work_session_service.shift_start_utc +
        core.utils.date_utils.to_utc_naive).
        """
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC sp_tiempos_operacion_modulo %s, %s, %s, %s",
                [fecha_inicio, module_id, shift_id, tipo_modulo],
            )

            cursor.nextset()
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            if not row:
                return {}

            indicators = translate_keys(dict(zip(columns, row)))
            indicators['module_id'] = int(indicators['module_id'])
            indicators['work_shift_id'] = int(indicators['work_shift_id'])
            indicators['elapsed_time_max_seconds'] = _to_float(indicators['elapsed_time_max_seconds'])
            indicators['work_break_seconds'] = _to_float(indicators['work_break_seconds'])
            indicators['module_downtime_seconds'] = _to_float(indicators['module_downtime_seconds'])
            indicators['has_no_records'] = bool(indicators['has_no_records'])

            return indicators

    @staticmethod
    def get_balance_summary(start_date, end_date, module_id=None):
        with connection.cursor() as cursor:
            cursor.execute(
                "EXEC sp_resumen_produccion %s, %s, %s",
                [start_date, end_date, module_id],
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

