"""
Persistencia de lo que recibe `integration/tep/send/`: el encabezado en
`TepSubmission` y cada item de `details` en `TepDetail`. La vista guarda el
envío como `pending` antes de llamar a SIESA y luego registra el resultado.
"""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.integration.models import TepDetail, TepSubmission, TepSubmissionStatus

# El `status` del encabezado de SIESA (0/1/2) se guarda como `document_status`.
_HEADER_FIELD_ALIASES = {"status": "document_status"}


def _model_values(model, values: dict, aliases: dict | None = None) -> dict:
    """Deja solo las llaves que son columnas del modelo (el resto, como
    `company_id` de un detalle, se hereda del encabezado y no se guarda)."""
    aliases = aliases or {}
    columns = {field.name for field in model._meta.concrete_fields}
    renamed = {aliases.get(key, key): value for key, value in values.items()}
    return {key: value for key, value in renamed.items() if key in columns and key != "id"}


@transaction.atomic
def create_pending_submission(
    header: dict, details: list[dict], flat_file_lines: list[str], user=None
) -> TepSubmission:
    """Guarda el encabezado (con `date` ya como `datetime.date`) y sus
    detalles con status `pending`."""
    submission = TepSubmission.objects.create(
        **_model_values(TepSubmission, header, _HEADER_FIELD_ALIASES),
        flat_file_lines=flat_file_lines,
        created_by=user,
        updated_by=user,
    )
    TepDetail.objects.bulk_create(
        [
            TepDetail(
                **{"record_number": number, **_model_values(TepDetail, detail)},
                submission=submission,
                created_by=user,
                updated_by=user,
            )
            for number, detail in enumerate(details, start=1)
        ]
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
