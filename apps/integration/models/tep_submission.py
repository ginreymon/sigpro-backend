from django.db import models

from core.models import TimeAuditModel, UserAuditModel


class TepSubmissionStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    SENT = "sent", "Enviado"
    FAILED = "failed", "Fallido"


class TepSubmission(UserAuditModel, TimeAuditModel):
    """Encabezado (registro 450) de lo que se envía a SIESA por
    `integration/tep/send/`, más el resultado del envío.

    Una fila por POST. Columnas alineadas con `header` del request (nombres
    de la API, en inglés) y con `HEADER_LAYOUT` de `builders/tep.py`; el
    `status` del encabezado de SIESA (0/1/2) se guarda como `document_status`
    para no chocar con el `status` del envío. Los items de `details` se
    guardan en `TepDetail`. Se guarda también cuando SIESA rechaza el envío.
    Sin restricción de unicidad: un mismo documento puede enviarse más de una
    vez (reintentos).
    """

    company_id = models.IntegerField()
    auto_consecutive = models.SmallIntegerField(default=1)
    operation_center_id = models.CharField(max_length=3)
    document_type_id = models.CharField(max_length=3, default="TPW")
    document_number = models.IntegerField(db_index=True)
    date = models.DateField()
    document_status = models.SmallIntegerField(default=1)
    printed = models.SmallIntegerField(default=0)
    notes = models.CharField(max_length=255, blank=True, default="")
    document_class_id = models.CharField(max_length=3, default="731")
    alternate_document = models.CharField(max_length=15, blank=True, default="")
    employee_id = models.CharField(max_length=15, blank=True, default="")
    work_center_id = models.CharField(max_length=15, blank=True, default="")
    shift = models.SmallIntegerField(default=1)

    flat_file_lines = models.JSONField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=TepSubmissionStatus.choices,
        default=TepSubmissionStatus.PENDING,
        db_index=True,
    )
    error_type = models.IntegerField(null=True, blank=True)
    error_detail = models.TextField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "integration_tep_submission"
        ordering = ["-created_at"]

    def __str__(self):
        return f"TEP {self.document_type_id} {self.document_number} [{self.status}]"
