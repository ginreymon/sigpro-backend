"""
Layout declarativo del documento TEP (Trabajo En Proceso): encabezado
(registro 450) + detalle/movimiento (registro 880).

Fuente: `assets/TP (Trabajo En Proceso).xlsm` (plano oficial de SIESA,
hojas "Encabezado"/"Detalle"), verificado byte a byte contra
`assets/MovInv 3.TXT`. Anchos totales confirmados: encabezado 347,
detalle 562.

Los `FieldSpec` conservan el nombre en español de SIESA en su propio plano
(`f350_id_co`, `f880_cant_rechazo_base`, etc., sin el prefijo `fNNN_`) para
poder cotejarlos contra el plano oficial. La API pública usa nombres en
inglés; `HEADER_API_TO_SIESA`/`DETAIL_API_TO_SIESA` los traducen al entrar.
"""

from __future__ import annotations

from apps.integration.builders.flat_file import FieldSpec, RecordLayout, build_line

HEADER_LAYOUT = RecordLayout(
    name="tep_encabezado",
    fields=(
        FieldSpec("numero_reg", 7, "numeric", True, "Numero de registro (secuencia)"),
        FieldSpec("tipo_reg", 4, "const", const_value="0450"),
        FieldSpec("subtipo_reg", 2, "const", const_value="02"),
        FieldSpec("version_reg", 2, "const", const_value="01"),
        FieldSpec("cia", 3, "numeric", True, "Compañia"),
        FieldSpec("consec_auto_reg", 1, "numeric", True, "0=manual, 1=automatico", default=1),
        FieldSpec("id_co", 3, "alpha", True, "Centro de operacion"),
        FieldSpec("id_tipo_docto", 3, "alpha", True, "Tipo de documento TEP", default="TPW"),
        FieldSpec("consec_docto", 8, "numeric", True, "Numero del documento TEP"),
        FieldSpec("fecha", 8, "date", True, "Fecha del documento AAAAMMDD"),
        FieldSpec("ind_estado", 1, "numeric", True, "0=elaboracion,1=aprobado,2=anulado", default=1),
        FieldSpec("ind_impresion", 1, "numeric", True, "0=no,1=si", default=0),
        FieldSpec("notas", 255, "alpha", False, "Notas del documento"),
        FieldSpec("id_clase_docto", 3, "alpha", True, "730=por empleado, 731=por centro de trabajo", default="731"),
        FieldSpec("docto_alterno", 15, "alpha", False, "Documento alterno"),
        FieldSpec("id_empleado", 15, "alpha", "dep", "Obligatorio si clase 730"),
        FieldSpec("id_centro_trabajo", 15, "alpha", "dep", "Obligatorio si clase 731"),
        FieldSpec("turno", 1, "numeric", True, "Numero de turno", default=1),
    ),
)
assert HEADER_LAYOUT.total_width == 347

DETAIL_LAYOUT = RecordLayout(
    name="tep_detalle",
    fields=(
        FieldSpec("numero_reg", 7, "numeric", True, "Numero de registro (secuencia)"),
        FieldSpec("tipo_reg", 4, "const", const_value="0880"),
        FieldSpec("subtipo_reg", 2, "const", const_value="00"),
        FieldSpec("version_reg", 2, "const", const_value="03"),
        FieldSpec("cia", 3, "numeric", True, "Compañia"),
        FieldSpec("id_co", 3, "alpha", True, "Centro de operacion"),
        FieldSpec("id_tipo_docto_tep", 3, "alpha", True, "Tipo de documento TEP (igual al encabezado)"),
        FieldSpec("consec_docto_tep", 8, "numeric", True, "Numero del documento TEP (igual al encabezado)"),
        FieldSpec("nro_registro", 10, "numeric", True, "Numero de registro del movimiento dentro del documento"),
        FieldSpec("id_tipo_docto_op", 3, "alpha", True, "Tipo de documento de la Orden de Produccion", default="OP"),
        FieldSpec("consec_docto_op", 8, "numeric", True, "Numero de la Orden de Produccion"),
        FieldSpec("id_item", 7, "numeric", "dep", "Item de la OP", default=0),
        FieldSpec("referencia_item", 50, "alpha", "dep", "Referencia del item"),
        FieldSpec("codigo_barras", 20, "alpha", "dep", "Codigo de barras del item"),
        FieldSpec("id_ext1", 20, "alpha", "dep", "Extension 1 del item"),
        FieldSpec("id_ext2", 20, "alpha", "dep", "Extension 2 del item"),
        FieldSpec("numero_operacion", 4, "numeric", True, "Numero de operacion de la OP"),
        FieldSpec("id_ctrabajo", 15, "alpha", True, "Centro de trabajo de la operacion"),
        FieldSpec("ind_tipo_hora", 1, "numeric", True, "0 ejecucion,1 maquina,2 alistamiento,3 paro,4 indirectas,9 ajuste", default=0),
        FieldSpec("id_labor", 15, "alpha", "dep", "Labor (si tipo de hora 0,2,4 y clase 730)"),
        FieldSpec("id_maquina", 15, "alpha", "dep", "Maquina (si tipo de hora 1)"),
        FieldSpec("ind_operacion_completa", 1, "numeric", True, "0=sin completar,1=completa", default=0),
        FieldSpec("cant_completa_base", 20, "quantity", False, "Cantidad completada", decimals=4, default=0.0),
        FieldSpec("cant_retrabajo_base", 20, "quantity", False, "Cantidad de retrabajo", decimals=4, default=0.0),
        FieldSpec("cant_rechazo_base", 20, "quantity", False, "Cantidad de rechazo (daños)", decimals=4, default=0.0),
        FieldSpec("id_motivo_rechazo", 2, "alpha", "dep", "Motivo de rechazo (obligatorio si hay cantidad de rechazo)"),
        FieldSpec("hora_inicial", 5, "time", "dep", "Hora inicial HH.MM", decimals=2, default=None),
        FieldSpec("hora_final", 5, "time", "dep", "Hora final HH.MM", decimals=2, default=None),
        FieldSpec("horas", 8, "time", "dep", "Total de horas del movimiento", decimals=2, default=0.0),
        FieldSpec("id_motivo_paro", 2, "alpha", "dep", "Motivo de paro (si tipo de hora 3)"),
        FieldSpec("notas", 255, "alpha", False, "Notas del movimiento"),
        FieldSpec("numero_operarios", 4, "numeric", "dep", "Numero de operarios (si tipo de hora 0 o 2)", default=1),
    ),
)
assert DETAIL_LAYOUT.total_width == 562

EMPLOYEE_DOCUMENT_CLASS = "730"
WORK_CENTER_DOCUMENT_CLASS = "731"

# Nombres publicos (API, en ingles) -> nombre del campo en el layout de SIESA.
# Solo se traducen en la frontera (`build_tep_document`): los layouts y el
# archivo plano resultante no cambian.
HEADER_API_TO_SIESA = {
    "company_id": "cia",
    "auto_consecutive": "consec_auto_reg",
    "operation_center_id": "id_co",
    "document_type_id": "id_tipo_docto",
    "document_number": "consec_docto",
    "date": "fecha",
    "status": "ind_estado",
    "printed": "ind_impresion",
    "notes": "notas",
    "document_class_id": "id_clase_docto",
    "alternate_document": "docto_alterno",
    "employee_id": "id_empleado",
    "work_center_id": "id_centro_trabajo",
    "shift": "turno",
}

DETAIL_API_TO_SIESA = {
    "company_id": "cia",
    "operation_center_id": "id_co",
    "tep_document_type_id": "id_tipo_docto_tep",
    "tep_document_number": "consec_docto_tep",
    "record_number": "nro_registro",
    "op_document_type_id": "id_tipo_docto_op",
    "op_document_number": "consec_docto_op",
    "item_id": "id_item",
    "item_reference": "referencia_item",
    "barcode": "codigo_barras",
    "extension1_id": "id_ext1",
    "extension2_id": "id_ext2",
    "operation_number": "numero_operacion",
    "operation_work_center_id": "id_ctrabajo",
    "hour_type": "ind_tipo_hora",
    "labor_id": "id_labor",
    "machine_id": "id_maquina",
    "operation_completed": "ind_operacion_completa",
    "completed_quantity": "cant_completa_base",
    "rework_quantity": "cant_retrabajo_base",
    "rejected_quantity": "cant_rechazo_base",
    "rejection_reason_id": "id_motivo_rechazo",
    "start_time": "hora_inicial",
    "end_time": "hora_final",
    "hours": "horas",
    "stop_reason_id": "id_motivo_paro",
    "notes": "notas",
    "operator_count": "numero_operarios",
}

_HEADER_INHERITED_FIELDS = {
    "id_tipo_docto_tep": "id_tipo_docto",
    "consec_docto_tep": "consec_docto",
}


def _to_siesa_names(values: dict, mapping: dict[str, str], record: str) -> dict:
    """Traduce las llaves de la API a los nombres del layout. Rechaza llaves
    desconocidas (incluidos los nombres viejos en español) en vez de
    ignorarlas en silencio: un campo ignorado saldría con su valor por defecto."""
    unknown = sorted(set(values) - set(mapping))
    if unknown:
        raise ValueError(f"Campos desconocidos en {record}: {', '.join(unknown)}")
    return {mapping[key]: value for key, value in values.items()}


def validate_header(values: dict) -> list[str]:
    """Regla de negocio propia de TEP (no es un campo por-ancho, es una
    dependencia cruzada entre `document_class_id` y `employee_id`/`work_center_id`).
    Recibe el encabezado con nombres de la API."""
    missing = []
    document_class = values.get("document_class_id", WORK_CENTER_DOCUMENT_CLASS)
    if document_class == EMPLOYEE_DOCUMENT_CLASS and not values.get("employee_id"):
        missing.append("employee_id (obligatorio si document_class_id=730)")
    if document_class == WORK_CENTER_DOCUMENT_CLASS and not values.get("work_center_id"):
        missing.append("work_center_id (obligatorio si document_class_id=731)")
    return missing


def build_tep_document(
    header: dict, details: list[dict], *, starting_sequence: int = 2
) -> list[str]:
    """Arma las líneas del documento TEP completo (1 encabezado + N
    detalles) — sin INICIO/cierre universal, eso lo agrega
    `siesa_webservice_client.build_import_xml`. `cia` e `id_co` se leen del
    encabezado y se copian a cada detalle si no vienen explícitos; lo mismo
    para el tipo/consecutivo de documento TEP (`id_tipo_docto`/
    `consec_docto` del encabezado -> `id_tipo_docto_tep`/`consec_docto_tep`
    de cada detalle).

    Lanza ValueError si falta algún campo obligatorio cruzado (ver
    `validate_header`) — no repite lo que ya valida `build_line` por ancho.
    """
    missing = validate_header(header)
    if missing:
        raise ValueError(
            "Faltan datos obligatorios en el encabezado TEP: " + ", ".join(missing)
        )

    header = _to_siesa_names(header, HEADER_API_TO_SIESA, "header")

    sequence = starting_sequence
    lines = [build_line(HEADER_LAYOUT, sequence, header)]
    sequence += 1

    for i, detail in enumerate(details, start=1):
        detail_values = _to_siesa_names(detail, DETAIL_API_TO_SIESA, "details")
        detail_values.setdefault("cia", header.get("cia"))
        detail_values.setdefault("id_co", header.get("id_co"))
        for local_field, header_field in _HEADER_INHERITED_FIELDS.items():
            detail_values.setdefault(local_field, header.get(header_field))
        detail_values.setdefault("nro_registro", i)

        lines.append(build_line(DETAIL_LAYOUT, sequence, detail_values))
        sequence += 1

    return lines
