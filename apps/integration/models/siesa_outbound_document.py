from django.db import models

from core.models import TimeAuditModel


class SiesaOutboundDocumentStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    SENDING = "sending", "Enviando"
    SENT = "sent", "Enviado"
    FAILED = "failed", "Fallido"
    POISONED = "poisoned", "Agotado (requiere revisión manual)"


class SiesaOutboundDocument(TimeAuditModel):
    """Outbox transaccional para documentos salientes hacia SIESA (WSUNOEE).

    Log transaccional inmutable, no una entidad editable por el usuario vía
    CRUD — a propósito NO hereda de `LocalBaseModel` (no aplica `rowid` de
    SIESA, no es una copia local de una tabla del ERP) ni de `ActiveModel`
    (el ciclo de vida lo maneja `status`, no soft-delete). Los registros solo
    cambian de estado, nunca se eliminan.

    Guarda las líneas de ancho fijo ya construidas (`flat_file_lines`), NO
    el XML final: el XML se arma en el momento de enviar
    (`siesa_webservice_client.build_import_xml`) para no persistir
    usuario/clave de SIESA en esta tabla.
    """

    document_type = models.CharField(max_length=50, db_index=True)
    idempotency_key = models.CharField(max_length=255, unique=True)
    flat_file_lines = models.JSONField()

    status = models.CharField(
        max_length=20,
        choices=SiesaOutboundDocumentStatus.choices,
        default=SiesaOutboundDocumentStatus.PENDING,
        db_index=True,
    )
    attempts = models.PositiveIntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True)

    error_type = models.IntegerField(null=True, blank=True)
    error_detail = models.TextField(null=True, blank=True)

    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "integration_siesa_outbound_document"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.document_type} [{self.status}] {self.idempotency_key}"
