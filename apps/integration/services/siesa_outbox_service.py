"""
Servicio de encolado del outbox de SIESA. Es la única puerta de entrada que
código de negocio (vistas, otros servicios) debe usar para pedir el envío de
un documento a SIESA — nunca deben llamar directo a
`siesa_webservice_client.send_xml`/`send_flat_file_lines`, porque eso es una
llamada de red síncrona (ver advertencia en ese módulo). `enqueue_document`
solo hace un INSERT local (rápido, transaccional) y devuelve; el envío real
lo hace `dispatch_siesa_outbox` (management command) en background.
"""

from __future__ import annotations

from apps.integration.models import SiesaOutboundDocument, SiesaOutboundDocumentStatus


def enqueue_document(
    document_type: str, idempotency_key: str, flat_file_lines: list[str]
) -> SiesaOutboundDocument:
    """Encola un documento para enviar a SIESA. Idempotente: si ya existe un
    registro con esta `idempotency_key`, lo devuelve tal cual (no lo
    duplica ni lo reescribe) — quien llama decide si eso es un error de su
    lado (ej. intentó encolar la misma OP/turno dos veces) o simplemente no
    hace nada más."""
    existing = SiesaOutboundDocument.objects.filter(idempotency_key=idempotency_key).first()
    if existing is not None:
        return existing

    return SiesaOutboundDocument.objects.create(
        document_type=document_type,
        idempotency_key=idempotency_key,
        flat_file_lines=flat_file_lines,
        status=SiesaOutboundDocumentStatus.PENDING,
    )
