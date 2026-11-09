"""
Column catalog for the efficiency report Excel (Confección and Estampación).

Each entry: (technical_name, "Excel header", "Spanish description").
`technical_name` is the key of the record returned by
fn_eficiencia_detallada_confeccion / fn_eficiencia_detallada_estampacion
(after translate_keys) plus the derived keys added by the exporter's
`_preprocess` (`sam`, `additional_minutes`). Only the technical name is internal:
the Excel shows the header and the description. The Excel only includes the
columns that have at least one value in the exported period, in the order defined
here; keys the catalog does not know are appended at the end so no SQL column is
silently dropped.
"""

REPORT_COLUMNS = [
    # Employee used as filter (only filled when the report is filtered by employee)
    ("employee_id",          "ID Empleado",        "Identificador interno del empleado por el que se filtró el reporte."),
    ("employee_id_number",   "Documento",          "Número de documento del empleado por el que se filtró el reporte."),
    ("employee_first_name",  "Nombre",             "Nombre del empleado por el que se filtró el reporte."),
    ("employee_last_name1",  "Apellido 1",         "Primer apellido del empleado por el que se filtró el reporte."),
    ("employee_last_name2",  "Apellido 2",         "Segundo apellido del empleado por el que se filtró el reporte."),
    ("employee_name",        "Nombre Completo",    "Nombre completo del empleado por el que se filtró el reporte."),

    # Jornada / module / shift
    ("shift_start_utc",      "Inicio Jornada",     "Fecha y hora local (UTC-5) en que inició la jornada de trabajo del módulo en el turno."),
    ("ended_at",             "Fin Jornada",        "Fecha y hora local (UTC-5) de fin de la jornada. Vacío si la jornada sigue abierta."),
    ("module_number",        "N° Módulo",          "Número del módulo (Confección) o máquina (Estampación)."),
    ("module_name",          "Módulo",             "Nombre del módulo o máquina."),
    ("module_location",      "Ubicación Módulo",   "Área de producción a la que pertenece el módulo."),
    ("shift_name",           "Turno",              "Nombre del turno de trabajo."),
    ("shift_start_time",     "Inicio Turno",       "Hora de inicio del turno, tomada del horario congelado al abrir la sesión."),
    ("shift_end_time",       "Fin Turno",          "Hora de fin del turno, tomada del horario congelado al abrir la sesión."),
    ("total_registers",      "N° Registros",       "Cantidad de asignaciones de módulo (actividades) que componen la jornada."),

    # People
    ("equivalent_employees", "Empleados Efectivos",
     "Número de empleados efectivos de la jornada: promedio ponderado por tiempo del peso de cada empleado "
     "(considera aprendices y minutos trabajados por hora). Es el valor usado en las metas de eficiencia y "
     "productividad; puede ser decimal y no es el conteo de personas."),
    ("employees",            "Operarios",
     "Empleados que participaron en la jornada, con su documento. Formato: NOMBRE DOCUMENTO; NOMBRE DOCUMENTO."),

    # Orders, references and SAM
    ("production_orders",    "Órdenes de Producción",
     "Órdenes (OP/PS) trabajadas en la jornada, sin repetir y separadas por punto y coma. Formato: OP 40056; PS 40789."),
    ("references",           "Referencias",
     "Referencias de las órdenes trabajadas en la jornada, sin repetir y separadas por punto y coma."),
    ("sam",                  "SAM",
     "Minutos estándar (SAM) de cada referencia, en el mismo orden que la columna Referencias y separados por punto y coma."),

    # Quantities
    ("total_ordered",        "Ordenadas",          "Suma de unidades ordenadas de los grupos de registros de la jornada."),
    ("total_completed",      "Completadas",        "Suma de unidades completadas (buenas)."),
    ("total_scrap",          "Bajas",              "Suma de unidades desechadas (bajas)."),
    ("total_rejected",       "Saldos",             "Suma de unidades rechazadas (saldos)."),
    ("total_produced",       "Total Producción",   "Completadas + bajas + saldos."),
    ("total_pieces_to_stamp","Piezas a Estampar",  "Estampación: unidades ordenadas por piezas a estampar de la referencia, sumadas por grupo."),
    ("avg_stamped_pieces",   "Prom. Piezas Estampadas", "Estampación: suma del promedio de piezas estampadas por grupo de registros."),

    # Targets, time and efficiency
    ("unit_target",          "Meta Unidades",      "Unidades que se debían producir según tiempo neto, SAM y empleados efectivos."),
    ("minutos_producidos",   "Minutos Producidos", "Unidades completadas multiplicadas por el SAM (minutos estándar)."),
    ("minutos_instalados",   "Minutos Instalados", "Tiempo neto disponible en minutos multiplicado por los empleados efectivos."),
    ("productividad",        "Productividad",      "Minutos producidos / minutos instalados (razón; 1 = 100 %)."),
    ("efficiency",           "Eficiencia (%)",     "Producción x 100 / meta de unidades. Confección: producción = completadas + bajas + saldos; Estampación: producción = completadas."),

    # Additional times and breaks
    ("additional_times",     "Tiempos Adicionales",
     "Estampación: tiempos adicionales (preparación o tareas manuales extra) declarados en los registros de la jornada, "
     "separados por punto y coma. Formato: código proceso xCantidad."),
    ("additional_minutes",   "Total Minutos Adicionales",
     "Estampación: total de tiempos adicionales en minutos, descontados del tiempo disponible."),
    ("breaks",               "Detalle Pausas",     "Pausas registradas en la jornada (nombre o motivo), separadas por punto y coma."),
    ("total_break_minutes",  "Min. Pausas",        "Total de minutos de pausa registrados en la jornada."),
]

CATALOG = {key: (label, desc) for key, label, desc in REPORT_COLUMNS}

# Returned by the SQL functions but not shown in the Excel: redundant ids, the
# period/shift duplicates, and values replaced by a derived column
# (additional_time_seconds -> additional_minutes).
EXCLUDED_FIELDS = {
    "period_start", "period_end", "shift_id",
    "module_id", "work_center_id", "work_shift_id", "module_operator_count",
    "net_seconds", "total_planned", "additional_time_seconds",
}

# Fields that need rounding: field -> decimal places
ROUND_FIELDS = {
    "equivalent_employees":    2,
    "unit_target":             0,
    "additional_minutes":      2,
    "avg_stamped_pieces":      2,
    "minutos_producidos":      2,
    "minutos_instalados":      2,
    "productividad":           4,
    "total_break_minutes":     2,
    "efficiency":              2,
}

# Fields that need UTC→local datetime conversion
UTC_FIELDS = {"shift_start_utc", "ended_at"}

UNKNOWN_COLUMN_DESCRIPTION = "Columna devuelta por la función SQL del reporte, sin descripción catalogada."
