import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.integration.models import SiesaOutboundDocument, SiesaOutboundDocumentStatus
from apps.integration.services.siesa_webservice_client import (
    SiesaWebserviceConfigError,
    SiesaWebserviceError,
    send_flat_file_lines,
)

logger = logging.getLogger("integration.dispatch_siesa_outbox")

# Cadencia de reintentos (intento -> espera desde el anterior), ver
# assets/SIESA_INTEGRATION_ARCHITECTURE.md §7. Tras el intento 5 sin éxito,
# el documento pasa a `poisoned` y requiere revisión manual.
_BACKOFF_MINUTES_BY_ATTEMPT = {
    1: 5,
    2: 30,
    3: 120,
    4: 720,
}
_MAX_ATTEMPTS = 5


class Command(BaseCommand):
    help = (
        "Envía a SIESA (WSUNOEE) los documentos pendientes/fallidos del outbox "
        "(SiesaOutboundDocument). Pensado para correr por Windows Task Scheduler, "
        "nunca desde un request de usuario (ver advertencia en "
        "siesa_webservice_client.py)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List documents that would be sent, without calling the webservice.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        now = timezone.now()

        due_documents = SiesaOutboundDocument.objects.filter(
            status__in=[
                SiesaOutboundDocumentStatus.PENDING,
                SiesaOutboundDocumentStatus.FAILED,
            ],
        ).exclude(
            status=SiesaOutboundDocumentStatus.FAILED, next_retry_at__gt=now,
        ).order_by("created_at")

        total = due_documents.count()
        logger.info("Due documents found: %s | dry_run=%s", total, dry_run)

        sent = 0
        failed = 0
        poisoned = 0

        for document in due_documents:
            logger.info(
                "[SEND] id=%s type=%s key=%s attempt=%s",
                document.id, document.document_type, document.idempotency_key,
                document.attempts + 1,
            )

            if dry_run:
                continue

            document.status = SiesaOutboundDocumentStatus.SENDING
            document.save(update_fields=["status", "updated_at"])

            try:
                result = send_flat_file_lines(document.flat_file_lines)
            except (SiesaWebserviceError, SiesaWebserviceConfigError) as exc:
                self._mark_failed(document, error_type=None, error_detail=str(exc))
                failed += 1
                if document.status == SiesaOutboundDocumentStatus.POISONED:
                    poisoned += 1
                logger.error("[ERROR] id=%s — %s", document.id, exc)
                continue

            if result.ok:
                document.status = SiesaOutboundDocumentStatus.SENT
                document.sent_at = timezone.now()
                document.error_type = None
                document.error_detail = None
                document.save(update_fields=["status", "sent_at", "error_type", "error_detail", "updated_at"])
                sent += 1
                logger.info("[SENT] id=%s", document.id)
            else:
                self._mark_failed(
                    document, error_type=result.error_type, error_detail=result.error_detail_xml
                )
                failed += 1
                if document.status == SiesaOutboundDocumentStatus.POISONED:
                    poisoned += 1
                logger.error(
                    "[SIESA_ERROR] id=%s error_type=%s", document.id, result.error_type
                )

        action = "Would send" if dry_run else "Sent"
        log_fn = logger.error if (failed and not dry_run) else logger.info
        log_fn(
            "%s %s | Failed %s | Poisoned %s | Due %s",
            action, sent, failed, poisoned, total,
        )

    @staticmethod
    def _mark_failed(document: SiesaOutboundDocument, *, error_type, error_detail) -> None:
        document.attempts += 1
        document.error_type = error_type
        document.error_detail = error_detail

        if document.attempts >= _MAX_ATTEMPTS:
            document.status = SiesaOutboundDocumentStatus.POISONED
            document.next_retry_at = None
        else:
            document.status = SiesaOutboundDocumentStatus.FAILED
            minutes = _BACKOFF_MINUTES_BY_ATTEMPT.get(document.attempts, _BACKOFF_MINUTES_BY_ATTEMPT[_MAX_ATTEMPTS - 1])
            document.next_retry_at = timezone.now() + timedelta(minutes=minutes)

        document.save(update_fields=["attempts", "status", "next_retry_at", "error_type", "error_detail", "updated_at"])
