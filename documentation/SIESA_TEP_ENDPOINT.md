# Endpoint — Enviar TEP a SIESA

`POST /api/v1/integration/tep/send/`

Arma un documento TEP (Trabajo En Proceso) a partir de un JSON, lo envía **sincrónicamente** al webservice WSUNOEE de SIESA y devuelve la respuesta real de SIESA en el mismo response HTTP.

**Es una llamada síncrona/bloqueante** (hasta ~30s mientras espera a SIESA): el worker de Django queda ocupado hasta que SIESA responde.

Implementación: [`apps/integration/views/siesa_tep_view.py`](views/siesa_tep_view.py) (`SiesaTepViewSet`).

---

## Autenticación

Requiere JWT (`IsAuthenticated`), igual que el resto de la API. Obtener el token primero:

```
POST /api/v1/auth/login/
{ "username": "...", "password": "..." }
```

Respuesta: `{ "access": "...", "refresh": "..." }`. Usar `access` como `Authorization: Bearer <access>` en la llamada al endpoint TEP.

## Configuración previa requerida

El servidor necesita estas variables en `backend/.env` (hoy no están seteadas → el endpoint responde `503`):

```
SIESA_WSUNOEE_WSDL_URL=
SIESA_WSUNOEE_CONNECTION_NAME=
SIESA_WSUNOEE_COMPANY_ID=
SIESA_WSUNOEE_USERNAME=
SIESA_WSUNOEE_PASSWORD=
```

## Request body

```json
{
  "header": {
    "company_id": 1,
    "operation_center_id": "001",
    "document_type_id": "TPW",
    "document_number": 999999,
    "date": "2026-09-25",
    "document_class_id": "731",
    "work_center_id": "CF005",
    "shift": 1,
    "notes": "PRUEBA POSTMAN - TEP"
  },
  "details": [
    {
      "op_document_type_id": "OP",
      "op_document_number": 40478,
      "operation_number": 30,
      "operation_work_center_id": "CF005",
      "completed_quantity": 0.088,
      "hours": 6.36
    }
  ]
}
```

- `header`: objeto obligatorio, un solo encabezado TEP (registro 450).
- `details`: lista obligatoria (mínimo 1 elemento), un item por cada movimiento/detalle (registro 880).
- `header.date`: string ISO `AAAA-MM-DD` (se convierte a `date` internamente). Si se omite, se usa la fecha de hoy.
- `header.document_class_id = "730"` (por empleado) requiere `employee_id`; `"731"` (por centro de trabajo, default) requiere `work_center_id`.
- Las llaves son en inglés. Una llave desconocida (incluidos los nombres viejos en español) responde `400`.

Campos completos (incluye opcionales no listados arriba: `employee_id`, `item_id`, `item_reference`, `barcode`, `rework_quantity`, `rejected_quantity` + `rejection_reason_id`, `start_time`/`end_time` en formato `HH.MM`, `stop_reason_id`, `operator_count`, `notes` del detalle, etc.) — ver [`apps/integration/builders/tep.py`](builders/tep.py): `HEADER_API_TO_SIESA`/`DETAIL_API_TO_SIESA` mapean cada llave de la API al campo del layout, y en `HEADER_LAYOUT`/`DETAIL_LAYOUT` cada `FieldSpec` (con el nombre SIESA original) documenta ancho, tipo, obligatoriedad y descripción, verificado byte a byte contra `assets/TP (Trabajo En Proceso).xlsm` y `assets/MovInv 3.TXT`.

## Guardado y validación de registros (`register_ids`)

Cada item de `details` puede (y desde Approval debe) traer, además de los campos de SIESA:

| Campo | Tipo | Descripción |
|---|---|---|
| `register_ids` | lista de enteros | Ids de los registros que respaldan el item (`ProductionRecord` o `StampingRecord`) |
| `origin_id` | 1 o 2 | 1 = producción, 2 = estampación; define en qué tabla se buscan los ids |
| `time_mode` | `real` o `standard` | Obligatorio. Tipo de tiempo con el que se integró (trazabilidad) |
| `real_seconds_by_unit` | número o null | `seconds_by_unit` de la OP al enviar (trazabilidad) |
| `sent_seconds_per_unit` | número o null (opcional) | segundos por unidad del tiempo ingresado por el usuario; si falta se deriva de `hours` y `completed_quantity` |

Estas llaves no van al archivo plano de SIESA. Antes de enviar, el backend valida en una transacción (con los registros bloqueados) que, por item:

1. `register_ids` sea una lista no vacía de enteros sin repetidos, y `origin_id` sea 1 o 2.
2. Todos los ids existan.
3. Pertenezcan a la OP del item (`op_document_number` y `op_document_type_id`).
4. Estén cerrados (`end_time` no nulo).
5. No hayan sido enviados antes con éxito (`tep_submission` de un envío `sent`).
6. `completed_quantity` coincida (tolerancia 0.01) con la suma de `completed_quantity` de los registros dividida por las piezas (`stamped_pieces` del SAM en estampación, 1 en producción).

Si alguna falla: `400` con `{"error": "register_ids invalidos", "details": ["details[0]: ..."]}` y no se guarda ni se envía nada.

Si todo es válido se guarda el envío como `pending` (`TepSubmission` + `TepDetail` + `TepDetailRecord`), se marca cada registro con `tep_submission`, se envía a SIESA y se actualiza el estado a `sent` o `failed`. La respuesta incluye `submission_id` y `document_number`. Los envíos rechazados por SIESA (`422`) o con error de red (`502`) también quedan guardados como `failed`.

### Valores fijos del encabezado

Si `header` no los trae, el backend completa: `document_type_id="TPW"`, `document_class_id="731"`, `auto_consecutive=0`, y asigna siempre `document_number` (consecutivo automático del backend, el mismo que se guarda y se envía; ver `TEP_SIESA_FLUJO.readme`), y desde `backend/.env`: `company_id` (`SIESA_TEP_COMPANY_ID`, por defecto `SIESA_WSUNOEE_COMPANY_ID` si es numérico) y `operation_center_id` (`SIESA_TEP_OPERATION_CENTER_ID`, por defecto `001`). Si falta algún campo obligatorio del layout, el endpoint responde `400` indicando cuál (antes se enviaba en blanco y lo rechazaba SIESA). Lo que venga en `header` tiene prioridad.

## Cambio de nombres: antes (español) → ahora (inglés)

Las llaves del request pasaron de los nombres en español del plano de SIESA a nombres en inglés. **El comportamiento no cambió**: mismas reglas de negocio, mismos valores por defecto, mismas respuestas y exactamente el mismo archivo plano enviado a SIESA. Solo cambia cómo se llama cada llave en el JSON.

Cómo funciona: `builders/tep.py` traduce las llaves de la API al nombre del layout de SIESA (`HEADER_API_TO_SIESA` / `DETAIL_API_TO_SIESA`) antes de armar cada línea. Los `FieldSpec` conservan el nombre original de SIESA, por lo que siguen cotejables contra el plano oficial.

Dos diferencias de comportamiento, ambas por el renombrado:

- Una llave desconocida —incluidos los nombres viejos en español— responde `400` (`Campos desconocidos en header: ...`). Antes se ignoraba en silencio y el campo salía con su valor por defecto. Un payload completo con nombres viejos falla primero en la validación del encabezado (`Faltan datos obligatorios ... work_center_id`), también con `400`.
- Los mensajes de validación citan los nombres nuevos (`work_center_id (obligatorio si document_class_id=731)`).

### Request antes

```json
{
  "header": {
    "cia": 1,
    "id_co": "001",
    "id_tipo_docto": "TPW",
    "consec_docto": 999999,
    "fecha": "2026-09-25",
    "id_clase_docto": "731",
    "id_centro_trabajo": "CF005",
    "turno": 1,
    "notas": "PRUEBA POSTMAN - TEP"
  },
  "details": [
    {
      "id_tipo_docto_op": "OP",
      "consec_docto_op": 40478,
      "numero_operacion": 30,
      "id_ctrabajo": "CF005",
      "cant_completa_base": 0.088,
      "horas": 6.36
    }
  ]
}
```

### Request ahora

```json
{
  "header": {
    "company_id": 1,
    "operation_center_id": "001",
    "document_type_id": "TPW",
    "document_number": 999999,
    "date": "2026-09-25",
    "document_class_id": "731",
    "work_center_id": "CF005",
    "shift": 1,
    "notes": "PRUEBA POSTMAN - TEP"
  },
  "details": [
    {
      "op_document_type_id": "OP",
      "op_document_number": 40478,
      "operation_number": 30,
      "operation_work_center_id": "CF005",
      "completed_quantity": 0.088,
      "hours": 6.36
    }
  ]
}
```

Ambos producen las mismas líneas de ancho fijo (encabezado de 347 caracteres y detalle de 562). El test `test_english_api_payload_builds_same_lines_as_siesa_layout_names` en `apps/integration/tests.py` verifica esa equivalencia.

### Equivalencia — `header`

| Antes (español) | Ahora (inglés) | Descripción |
|---|---|---|
| `cia` | `company_id` | Compañía |
| `consec_auto_reg` | `auto_consecutive` | 0=manual, 1=automático (default 1) |
| `id_co` | `operation_center_id` | Centro de operación |
| `id_tipo_docto` | `document_type_id` | Tipo de documento TEP (default `TPW`) |
| `consec_docto` | `document_number` | Número del documento TEP |
| `fecha` | `date` | Fecha `AAAA-MM-DD` (default hoy) |
| `ind_estado` | `status` | 0=elaboración, 1=aprobado, 2=anulado (default 1) |
| `ind_impresion` | `printed` | 0=no, 1=sí (default 0) |
| `notas` | `notes` | Notas del documento |
| `id_clase_docto` | `document_class_id` | 730=por empleado, 731=por centro de trabajo (default 731) |
| `docto_alterno` | `alternate_document` | Documento alterno |
| `id_empleado` | `employee_id` | Obligatorio si clase 730 |
| `id_centro_trabajo` | `work_center_id` | Obligatorio si clase 731 |
| `turno` | `shift` | Número de turno (default 1) |

### Equivalencia — `details[]`

| Antes (español) | Ahora (inglés) | Descripción |
|---|---|---|
| `cia` | `company_id` | Si se omite, hereda el del encabezado |
| `id_co` | `operation_center_id` | Si se omite, hereda el del encabezado |
| `id_tipo_docto_tep` | `tep_document_type_id` | Si se omite, hereda `document_type_id` del encabezado |
| `consec_docto_tep` | `tep_document_number` | Si se omite, hereda `document_number` del encabezado |
| `nro_registro` | `record_number` | Si se omite, es la posición del detalle (1, 2, ...) |
| `id_tipo_docto_op` | `op_document_type_id` | Tipo de documento de la OP (default `OP`) |
| `consec_docto_op` | `op_document_number` | Número de la OP |
| `id_item` | `item_id` | Ítem de la OP |
| `referencia_item` | `item_reference` | Referencia del ítem |
| `codigo_barras` | `barcode` | Código de barras del ítem |
| `id_ext1` | `extension1_id` | Extensión 1 del ítem |
| `id_ext2` | `extension2_id` | Extensión 2 del ítem |
| `numero_operacion` | `operation_number` | Número de operación de la OP |
| `id_ctrabajo` | `operation_work_center_id` | Centro de trabajo de la operación |
| `ind_tipo_hora` | `hour_type` | 0 ejecución, 1 máquina, 2 alistamiento, 3 paro, 4 indirectas, 9 ajuste (default 0) |
| `id_labor` | `labor_id` | Labor (tipo de hora 0, 2, 4 y clase 730) |
| `id_maquina` | `machine_id` | Máquina (tipo de hora 1) |
| `ind_operacion_completa` | `operation_completed` | 0=sin completar, 1=completa (default 0) |
| `cant_completa_base` | `completed_quantity` | Cantidad completada |
| `cant_retrabajo_base` | `rework_quantity` | Cantidad de retrabajo |
| `cant_rechazo_base` | `rejected_quantity` | Cantidad de rechazo |
| `id_motivo_rechazo` | `rejection_reason_id` | Obligatorio si hay cantidad de rechazo |
| `hora_inicial` | `start_time` | Formato `HH.MM` |
| `hora_final` | `end_time` | Formato `HH.MM` |
| `horas` | `hours` | Total de horas del movimiento. La API recibe **horas decimales** (`1.5` = 1 h 30 min); el backend las convierte a `HH.MM` para SIESA (`1.30`) con `decimal_hours_to_hhmm`. `TepDetail.hours` guarda el valor decimal. |
| `id_motivo_paro` | `stop_reason_id` | Si tipo de hora 3 |
| `notas` | `notes` | Notas del movimiento |
| `numero_operarios` | `operator_count` | Si tipo de hora 0 o 2 (default 1) |

### Sin cambios

- **Response:** `ok`, `error_type` y `error_detail_xml` ya estaban en inglés.
- **URL, autenticación y códigos de estado:** iguales.
- **Campos internos del layout** (`numero_reg`, `tipo_reg`, `subtipo_reg`, `version_reg`): no se envían en el request, los fija el builder.

### Clientes que hay que migrar

Cualquier cliente que siga enviando los nombres viejos recibirá `400`. El único cliente conocido en este repo, `Integration/send_tep_reports.py`, ya fue actualizado.

## Respuestas

| Status | Cuerpo | Significado |
|---|---|---|
| `200 OK` | `{"ok": true, "error_type": null, "error_detail_xml": null}` | SIESA aceptó el documento. |
| `422 Unprocessable Entity` | `{"ok": false, "error_type": N, "error_detail_xml": "..."}` | SIESA procesó la llamada pero reportó un error de negocio (OP inválida, centro de trabajo inválido, etc.) — respuesta esperada, no es un bug del endpoint. |
| `400 Bad Request` | `{"error": "..."}` | Body inválido: falta `header`/`details`, `date` mal formateada, llave desconocida, o falta algún campo obligatorio cruzado del layout TEP. |
| `503 Service Unavailable` | `{"error": "..."}` | Faltan las variables `SIESA_WSUNOEE_*` en el servidor. |
| `502 Bad Gateway` | `{"error": "..."}` | Falló la llamada SOAP/red hacia SIESA (timeout, WSDL inválido, etc.). |

Las líneas de ancho fijo enviadas a SIESA (encabezado + detalles) se guardan en `TepSubmission.flat_file_lines` para auditoría; no se devuelven en la respuesta.
