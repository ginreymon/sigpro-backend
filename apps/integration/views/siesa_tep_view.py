import datetime as dt

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.exceptions import error_response

from apps.integration.builders.tep import build_tep_document
from apps.integration.services.tep_submission_service import (
    RecordValidationError,
    mark_submission_result,
    register_submission,
    split_record_references,
    with_header_defaults,
)
from apps.integration.services.siesa_webservice_client import (
    SiesaWebserviceConfig,
    SiesaWebserviceConfigError,
    SiesaWebserviceError,
    send_flat_file_lines,
)


class SiesaTepViewSet(viewsets.ViewSet):
    """Arma un documento TEP (Trabajo En Proceso) a partir de un JSON y lo
    envia a SIESA (WSUNOEE), devolviendo la respuesta real de SIESA en el
    mismo request.

    Es una llamada sincrona que bloquea hasta ~30s por request (ver
    advertencia en `siesa_webservice_client.py`).
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="tep/send")
    def send(self, request):
        header = request.data.get("header")
        details = request.data.get("details")

        if not isinstance(header, dict) or not header:
            return error_response(
                "'header' es requerido (objeto)", code="invalid_tep_request",
                legacy={"error": "'header' es requerido (objeto)"},
            )
        if not isinstance(details, list) or not details:
            return error_response(
                "'details' es requerido (lista no vacia)", code="invalid_tep_request",
                legacy={"error": "'details' es requerido (lista no vacia)"},
            )

        header = with_header_defaults(dict(header))
        date = header["date"]
        if isinstance(date, str):
            try:
                header["date"] = dt.date.fromisoformat(date)
            except ValueError:
                return error_response(
                    "'header.date' debe tener formato AAAA-MM-DD", code="invalid_tep_request",
                    legacy={"error": "'header.date' debe tener formato AAAA-MM-DD"},
                )

        # register_ids/origin_id no son de SIESA: se separan antes de armar el documento.
        details, references = split_record_references(details)

        try:
            lines = build_tep_document(header, details)
        except ValueError as exc:
            return error_response(str(exc), code="invalid_tep_document", legacy={"error": str(exc)})

        try:
            cfg = SiesaWebserviceConfig.from_settings()
        except SiesaWebserviceConfigError as exc:
            return error_response(
                str(exc), status_code=status.HTTP_503_SERVICE_UNAVAILABLE, code="siesa_not_configured",
                legacy={"error": str(exc)},
            )

        # Valida los register_ids y guarda antes de llamar a SIESA: queda
        # registro aunque falle el envío.
        try:
            submission = register_submission(
                header, details, lines, user=request.user, references=references
            )
        except RecordValidationError as exc:
            return error_response(
                "register_ids invalidos", code="invalid_register_ids",
                errors={"register_ids": exc.errors},
                legacy={"error": "register_ids invalidos", "details": exc.errors},
            )

        try:
            result = send_flat_file_lines(lines, cfg=cfg)
        except SiesaWebserviceError as exc:
            mark_submission_result(submission, ok=False, error_detail=str(exc))
            return error_response(
                str(exc), status_code=status.HTTP_502_BAD_GATEWAY, code="siesa_unreachable",
                legacy={"error": str(exc)},
            )

        mark_submission_result(
            submission, ok=result.ok, error_type=result.error_type, error_detail=result.error_detail_xml
        )

        payload = {
            "submission_id": submission.id,
            "ok": result.ok,
            "error_type": result.error_type,
            "error_detail_xml": result.error_detail_xml,
        }

        if result.ok:
            return Response(payload, status=status.HTTP_200_OK)

        # SIESA rejected the document: an error response that still carries its result.
        return error_response(
            f"SIESA rechazó el envío (tipo de error {result.error_type}).",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="siesa_rejected",
            extra=payload,
        )
