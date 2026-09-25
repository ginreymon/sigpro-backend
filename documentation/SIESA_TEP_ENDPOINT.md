# Endpoint — Enviar TEP a SIESA

`POST /api/v1/integration/tep/send/`

Arma un documento TEP (Trabajo En Proceso) a partir de un JSON, lo envía **sincrónicamente** al webservice WSUNOEE de SIESA y devuelve la respuesta real de SIESA en el mismo response HTTP.

**Es una llamada síncrona/bloqueante** (hasta ~30s mientras espera a SIESA) — a propósito NO usa el outbox asíncrono ya existente en el proyecto (ver [`apps/integration/services/siesa_outbox_service.py`](services/siesa_outbox_service.py) + el comando `dispatch_siesa_outbox`, disparado por tarea programada), mismo patrón que ya usa el comando `python manage.py test_siesa_webservice`. Sirve bien para envíos puntuales/bajo demanda; si este endpoint llega a recibir volumen real y sostenido de producción, lo arquitectónicamente correcto es migrar ese flujo al outbox (asíncrono, no bloquea el worker de Django).

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

- `header`: objeto obligatorio, un solo encabezado TEP (registro 450).
- `details`: lista obligatoria (mínimo 1 elemento), un item por cada movimiento/detalle (registro 880).
- `header.fecha`: string ISO `AAAA-MM-DD` (se convierte a `date` internamente). Si se omite, se usa la fecha de hoy.
- `header.id_clase_docto = "730"` (por empleado) requiere `id_empleado`; `"731"` (por centro de trabajo, default) requiere `id_centro_trabajo`.

Campos completos (incluye opcionales no listados arriba: `id_empleado`, `id_item`, `referencia_item`, `codigo_barras`, `cant_retrabajo_base`, `cant_rechazo_base` + `id_motivo_rechazo`, `hora_inicial`/`hora_final` en formato `HH.MM`, `id_motivo_paro`, `numero_operarios`, `notas` del detalle, etc.) — ver [`apps/integration/builders/tep.py`](builders/tep.py), `HEADER_LAYOUT` y `DETAIL_LAYOUT`: cada `FieldSpec` documenta nombre, ancho, tipo, obligatoriedad y descripción, verificado byte a byte contra `assets/TP (Trabajo En Proceso).xlsm` y `assets/MovInv 3.TXT`.

## Respuestas

| Status | Cuerpo | Significado |
|---|---|---|
| `200 OK` | `{"ok": true, "error_type": null, "error_detail_xml": null, "flat_file_lines": [...]}` | SIESA aceptó el documento. |
| `422 Unprocessable Entity` | `{"ok": false, "error_type": N, "error_detail_xml": "...", "flat_file_lines": [...]}` | SIESA procesó la llamada pero reportó un error de negocio (OP inválida, centro de trabajo inválido, etc.) — respuesta esperada, no es un bug del endpoint. |
| `400 Bad Request` | `{"error": "..."}` | Body inválido: falta `header`/`details`, `fecha` mal formateada, o falta algún campo obligatorio cruzado del layout TEP. |
| `503 Service Unavailable` | `{"error": "..."}` | Faltan las variables `SIESA_WSUNOEE_*` en el servidor. |
| `502 Bad Gateway` | `{"error": "..."}` | Falló la llamada SOAP/red hacia SIESA (timeout, WSDL inválido, etc.). |

`flat_file_lines` son las líneas de ancho fijo ya armadas (encabezado + detalles), útiles para depurar qué se envió exactamente.

## Probar con Postman

Importar `apps/integration/postman/SIESA_TEP.postman_collection.json`:

1. **Login** — completar usuario/clave reales en el body, ejecutar. El test script guarda el `access` token en la variable de colección `access_token` automáticamente.
2. **TEP - Send** — trae un body de ejemplo con valores demo (`consec_docto=999999`, fácil de ubicar/ignorar en SIESA) — reemplazar por los datos reales antes de un envío real — y el header `Authorization: Bearer {{access_token}}` ya resuelto. Ejecutar y revisar la respuesta.

Variable de colección `base_url` (default `http://localhost:8000`) — cambiar si el backend corre en otro host/puerto.
