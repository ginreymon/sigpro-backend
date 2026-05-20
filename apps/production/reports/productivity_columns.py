_EMPLOYEE_FIELDS = [
    ("employee_id_number",       "Documento"),
    ("employee_first_name",      "Nombre"),
    ("employee_last_name1",      "Apellido 1"),
    ("employee_last_name2",      "Apellido 2"),
]

_SHARED_COLUMNS = [
    ("module_number",            "N° Módulo"),
    ("module_name",              "Módulo"),
    ("work_center_code",         "Cód. Centro"),
    ("work_center_name",         "Centro de Trabajo"),
    ("shift_name",               "Turno"),
    ("shift_start_time",         "Inicio Turno"),
    ("shift_end_time",           "Fin Turno"),
    ("shift_total_seconds",      "Min. Turno"),
    ("op_number",                "N° OP"),
    ("op_type",                  "Tipo OP"),
    ("sku_reference",            "Referencia"),
    ("sku_description",          "Descripción"),
    ("sku_size",                 "Talla"),
    ("sku_color",                "Color"),
    ("sku_inv_type",             "Tipo Inv."),
    ("sku_sam",                  "SAM"),
    ("employee_count",           "N° Operarios"),
    ("total_records",            "Registros"),
    ("total_ordered",            "Ordenado"),
    ("total_planned",            "Planeado"),
    ("total_completed",          "Completado"),
    ("total_scrap",              "Desechos"),
    ("total_rejected",           "Rechazos"),
    ("total_sam_earned",         "SAM Ganado"),
    ("total_productive_seconds", "Min. Productivos"),
    ("total_break_seconds",      "Min. Pausa"),
    ("total_activity_seconds",   "Min. Actividad"),
    ("elapsed_shift_seconds",    "Min. Transcurridos"),
    ("efficiency",               "Eficiencia"),
    ("first_record_start",       "Primer Registro (Inicio)"),
    ("last_record_end",          "Último Registro (Cierre)"),
]

SUMMARY_COLUMNS = _SHARED_COLUMNS 

EMPLOYEE_COLUMNS = _EMPLOYEE_FIELDS + _SHARED_COLUMNS 