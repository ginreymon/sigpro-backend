"""
Column definitions for sp_reporte_eficiencia_detallada_confeccion Excel export.
Each entry: (field_key_after_translate_keys, "Excel header label")
"""

_EMPLOYEE_FIELDS = [
    ("employee_id_number",  "Documento"),
    ("employee_first_name", "Nombre"),
    ("employee_last_name1", "Apellido 1"),
    ("employee_last_name2", "Apellido 2"),
]

_SHARED_COLUMNS = [
    ("shift_start_utc",    "Inicio Jornada"),
    ("ended_at",           "Fin Jornada"),
    ("module_number",      "N° Módulo"),
    ("module_name",        "Módulo"),
    ("shift_name",         "Turno"),
    ("shift_start_time",   "Inicio Turno"),
    ("shift_end_time",     "Fin Turno"),
    ("total_employees",    "N° Operarios (ef.)"),
    ("total_ordered",      "Ordenadas"),
    ("total_planned",      "Planeadas"),
    ("total_completed",    "Completadas"),
    ("total_scrap",        "Bajas"),
    ("total_rejected",     "Saldos"),
    ("total_produced",     "Total Producción"),
    ("unit_target",        "Meta Unidades"),
    ("breaks_text",        "Detalle Pausas"),
    ("total_break_minutes","Min. Pausas"),   
    ("efficiency",         "Eficiencia (%)"),
    ("employees_text",     "Operarios"),
]

# Stamping only: appended when the report rows carry `additional_times`.
ADDITIONAL_TIMES_COLUMN = ("additional_times_text", "Tiempos Adicionales")

SUMMARY_COLUMNS  = _SHARED_COLUMNS
EMPLOYEE_COLUMNS = _EMPLOYEE_FIELDS + _SHARED_COLUMNS

# Fields that need rounding: field -> decimal places
ROUND_FIELDS = {
    "unit_target": 0,
    "efficiency":  2,
}

# Fields that need UTC→local datetime conversion
UTC_FIELDS = {"shift_start_utc", "ended_at"}

# Fields computed from other fields (not present in raw record)
COMPUTED_FIELDS = {"breaks_text", "employees_text", "additional_times_text"}
