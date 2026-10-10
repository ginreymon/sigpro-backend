import json
from django.db import connection
from apps.common.mappers.recursive_mapper import translate_keys
from apps.common.repositories.productivity_repository import BaseProductivityRepository, rows_with_json


def _to_float(value):
    return float(value) if value is not None else None


class ProductivityRepository(BaseProductivityRepository):
    efficiency_period_sp = "sp_eficiencia_periodo_produccion"
    module_shift_summary_sp = "sp_resumen_modulos_eficiencia_turno"
    module_efficiency_sp = "sp_eficiencia_modulos_produccion"
    shift_summary_sp = "sp_resumen_produccion_turno"

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
    def get_tiempos_operacion_modulo(fecha_inicio, module_id, shift_id, tipo_modulo='production'):
        """
        EXEC sp_tiempos_operacion_modulo — only the indicators (result set 2)
        are needed; the detail (result set 1) is discarded.

        fecha_inicio must be the shift start already converted to UTC naive
        (see apps.production.services.work_session_service.shift_start_utc +
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
            return rows_with_json(cursor, "records_detail")
