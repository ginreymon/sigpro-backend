"""
Persistencia de lo que recibe `integration/tep/send/`: el encabezado en
`TepSubmission`, cada item de `details` en `TepDetail` y los registros de
producción/estampación que lo respaldan en `TepDetailRecord`.

`register_submission` valida los `register_ids` de cada item (con los
registros bloqueados dentro de la transacción) y guarda el envío como
`pending`; la vista lo llama antes de enviar a SIESA y luego registra el
resultado con `mark_submission_result`.
"""

from __future__ import annotations

from decimal import Decimal
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.integration.models import (
    TepDetail,
    TepDetailRecord,
    TepSubmission,
    TepSubmissionStatus,
)
from apps.production.models import ProductionRecord
from apps.stamping.models import StampingRecord

# settings.TIME_ZONE es UTC: la fecha del documento se calcula en hora local
# para que un envío en la noche no salga con la fecha del día siguiente.
SUBMISSION_TIME_ZONE = ZoneInfo("America/Bogota")

# El `status` del encabezado de SIESA (0/1/2) se guarda como `document_status`.
_HEADER_FIELD_ALIASES = {"status": "document_status"}

# origin_id (production_production_area.id) -> modelo de registros.
RECORD_MODELS = {1: ProductionRecord, 2: StampingRecord}

# Piezas por unidad de cada registro (misma regla que fn_totales_registrados_por_op:
# producción 1, estampación stamped_pieces del SAM, 1 si es nulo).
_PIECES_FIELD = {1: None, 2: "stamping_reference_sam__stamped_pieces"}

# Llaves de cada item de `details` que no son de SIESA: se separan antes de
# armar el documento TEP.
RECORD_KEYS = ("register_ids", "origin_id")

# Diferencia máxima admitida entre la cantidad enviada y la de los registros.
QUANTITY_TOLERANCE = Decimal("0.01")


class RecordValidationError(Exception):
    """Los `register_ids` de uno o más items no son válidos."""

    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def with_header_defaults(header: dict) -> dict:
    """Completa los valores fijos del encabezado que el frontend no manda.
    Lo que venga en `header` tiene prioridad; si no trae `date` (o es null),
    se usa el día en que se hace el envío. `company_id` y `operation_center_id` salen de la configuración (si está
    definida)."""
    defaults: dict = {
        "document_type_id": "TPW",
        "document_class_id": "731",
        "auto_consecutive": 1,
        "document_number": 0,
    }
    company_id = str(getattr(settings, "SIESA_TEP_COMPANY_ID", "") or "")
    if company_id.isdigit():
        defaults["company_id"] = int(company_id)
    operation_center_id = getattr(settings, "SIESA_TEP_OPERATION_CENTER_ID", "")
    if operation_center_id:
        defaults["operation_center_id"] = operation_center_id
    merged = {**defaults, **header}
    if not merged.get("date"):
        merged["date"] = timezone.localtime(timezone.now(), SUBMISSION_TIME_ZONE).date()
    return merged


def _model_values(model, values: dict, aliases: dict | None = None) -> dict:
    """Deja solo las llaves que son columnas del modelo (el resto, como
    `company_id` de un detalle, se hereda del encabezado y no se guarda)."""
    aliases = aliases or {}
    columns = {field.name for field in model._meta.concrete_fields}
    renamed = {aliases.get(key, key): value for key, value in values.items()}
    return {key: value for key, value in renamed.items() if key in columns and key != "id"}


def split_record_references(details: list) -> tuple[list, list[dict]]:
    """Separa de cada item de `details` las llaves `register_ids`/`origin_id`.

    Devuelve (items sin esas llaves, referencias por item). Un item que no es
    objeto se deja tal cual; lo rechaza la validación posterior.
    """
    clean, references = [], []
    for detail in details:
        if not isinstance(detail, dict):
            clean.append(detail)
            references.append({})
            continue
        clean.append({key: value for key, value in detail.items() if key not in RECORD_KEYS})
        references.append({key: detail.get(key) for key in RECORD_KEYS})
    return clean, references


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _to_decimal(value) -> Decimal | None:
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _validate_item(index: int, detail, reference: dict) -> list[str]:
    """Valida los `register_ids` de un item. Debe llamarse dentro de una
    transacción: bloquea las filas de los registros (`select_for_update`)."""
    label = f"details[{index}]"
    if not isinstance(detail, dict):
        return [f"{label}: debe ser un objeto"]

    ids = reference.get("register_ids")
    origin_id = reference.get("origin_id")

    errors = []
    if origin_id not in RECORD_MODELS:
        errors.append(f"{label}: 'origin_id' debe ser {' o '.join(map(str, RECORD_MODELS))}")
    if not isinstance(ids, list) or not ids or not all(_is_int(i) for i in ids):
        errors.append(f"{label}: 'register_ids' es requerido (lista de enteros no vacía)")
    elif len(set(ids)) != len(ids):
        errors.append(f"{label}: 'register_ids' tiene ids repetidos")
    if errors:
        return errors

    pieces_field = _PIECES_FIELD[origin_id]
    fields = ["id", "op_number", "op_type", "end_time", "completed_quantity", "tep_submission__status"]
    if pieces_field:
        fields.append(pieces_field)
    records = {
        record["id"]: record
        for record in RECORD_MODELS[origin_id].objects.select_for_update().filter(id__in=ids).values(*fields)
    }

    missing = sorted(set(ids) - set(records))
    if missing:
        errors.append(f"{label}: no existen los registros {missing}")

    op_number = detail.get("op_document_number")
    op_type = detail.get("op_document_type_id", "OP")
    wrong_op = sorted(i for i, r in records.items() if r["op_number"] != op_number or r["op_type"] != op_type)
    if wrong_op:
        errors.append(f"{label}: los registros {wrong_op} no son de la OP {op_type} {op_number}")

    open_records = sorted(i for i, r in records.items() if r["end_time"] is None)
    if open_records:
        errors.append(f"{label}: los registros {open_records} siguen abiertos (sin end_time)")

    already_sent = sorted(
        i for i, r in records.items() if r["tep_submission__status"] == TepSubmissionStatus.SENT
    )
    if already_sent:
        errors.append(f"{label}: los registros {already_sent} ya fueron enviados")

    if not missing:
        pieces = max([(r.get(pieces_field) if pieces_field else 1) or 1 for r in records.values()])
        expected = sum((r["completed_quantity"] for r in records.values()), Decimal("0")) / Decimal(pieces)
        sent = _to_decimal(detail.get("completed_quantity", 0))
        if sent is None or abs(sent - expected) > QUANTITY_TOLERANCE:
            errors.append(
                f"{label}: 'completed_quantity' ({detail.get('completed_quantity', 0)}) no coincide con "
                f"la de los registros ({expected.quantize(Decimal('0.0001'))})"
            )

    return errors


@transaction.atomic
def register_submission(
    header: dict,
    details: list[dict],
    flat_file_lines: list[str],
    user=None,
    references: list[dict] | None = None,
) -> TepSubmission:
    """Valida los `register_ids` y guarda el encabezado (con `date` ya como
    `datetime.date`), sus detalles y los registros que los respaldan, con
    status `pending`. Marca cada registro con el envío (`tep_submission`) y
    como procesado (`tep_processed`).

    Lanza RecordValidationError (sin guardar nada) si algún id no es válido.
    """
    references = references or [{}] * len(details)

    errors: list[str] = []
    for index, (detail, reference) in enumerate(zip(details, references)):
        errors.extend(_validate_item(index, detail, reference))
    if errors:
        raise RecordValidationError(errors)

    submission = TepSubmission.objects.create(
        **_model_values(TepSubmission, header, _HEADER_FIELD_ALIASES),
        flat_file_lines=flat_file_lines,
        created_by=user,
        updated_by=user,
    )
    for number, (detail, reference) in enumerate(zip(details, references), start=1):
        saved = TepDetail.objects.create(
            **{"record_number": number, **_model_values(TepDetail, detail)},
            submission=submission,
            created_by=user,
            updated_by=user,
        )
        ids = reference["register_ids"]
        TepDetailRecord.objects.bulk_create(
            [TepDetailRecord(detail=saved, origin_id=reference["origin_id"], record_id=i) for i in ids]
        )
        RECORD_MODELS[reference["origin_id"]].objects.filter(id__in=ids).update(
            tep_submission=submission, tep_processed=True
        )
    return submission


def mark_submission_result(
    submission: TepSubmission,
    *,
    ok: bool,
    error_type: int | None = None,
    error_detail: str | None = None,
) -> TepSubmission:
    """Registra el resultado del envío a SIESA (también cuando falla)."""
    submission.status = TepSubmissionStatus.SENT if ok else TepSubmissionStatus.FAILED
    submission.error_type = error_type
    submission.error_detail = error_detail
    submission.sent_at = timezone.now() if ok else None
    submission.save(update_fields=["status", "error_type", "error_detail", "sent_at", "updated_at"])
    return submission
