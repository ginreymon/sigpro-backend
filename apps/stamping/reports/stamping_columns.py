"""
Column catalog of the Stamping efficiency report Excel (kept apart from the shared
Confección catalog in apps/production/reports/productivity_columns.py).

Each entry: (technical_name, "Excel header", "Spanish description"). Keys are either
returned by fn_eficiencia_detallada_estampacion (after translate_keys) or derived by
the stamping exporter (elapsed_hours, shift_label, shift_end, pieces_produced,
target_pieces). Minutes and productivity come straight from the SQL
(minutos_producidos, minutos_instalados, productividad), as in Confección.
"""

from apps.production.reports.productivity_columns import CATALOG


def _same(key: str) -> tuple:
    return CATALOG[key]


STAMPING_COLUMNS = [
    ("module_location", *_same("module_location")),
    ("shift_start_utc",  *_same("shift_start_utc")),
    ("ended_at",         *_same("ended_at")),
    ("elapsed_hours",    "Horas Transcurridas", "Horas entre el inicio y el fin de la jornada."),
    ("module_number",    *_same("module_number")),
    ("module_name",      *_same("module_name")),
    ("shift_label",      *_same("shift_label")),
    ("total_registers",  *_same("total_registers")),
    ("equivalent_employees", *_same("equivalent_employees")),
    ("employees",        *_same("employees")),
    ("production_orders", *_same("production_orders")),
    ("references",       *_same("references")),
    ("sam",              *_same("sam")),
    ("additional_minutes", *_same("additional_minutes")),
    ("additional_times", *_same("additional_times")),
    ("total_break_minutes", *_same("total_break_minutes")),
    ("breaks",           *_same("breaks")),
    ("pieces_produced",  "Piezas Producidas", "Cantidades completadas convertidas en piezas."),
    ("target_pieces",    "Meta Piezas",
     "Piezas que se debían estampar según tiempo neto, SAM y operarios efectivos."),
    ("avg_stamped_pieces", *_same("avg_stamped_pieces")),
    ("minutos_producidos", *_same("minutos_producidos")),
    ("minutos_instalados", *_same("minutos_instalados")),
    ("productividad",    *_same("productividad")),
    ("efficiency",       *_same("efficiency")),
]

STAMPING_LABELS = {key: label for key, label, _ in STAMPING_COLUMNS}

# "Detalle registros" sheet: fn_reporte_registros columns, in the order requested for Stamping.
STAMPING_RECORD_FIELDS = [
    "id_registro", "area", "horario", "fecha", "hora_registro", "documento", "referencia", "sam",
    "maquina", "numero_modulo", "operarios", "minutos_pausas", "detalle_pausas",
    "total_minutos_adicionales", "tiempos_adicionales",
]
