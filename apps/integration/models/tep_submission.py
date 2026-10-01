from django.conf import settings
from django.db import models

from core.models import TimeAuditModel


class TepSubmissionStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    SENT = "sent", "Enviado"
    FAILED = "failed", "Fallido"


class TepSubmission(TimeAuditModel):
    """Registro de lo que se envía a SIESA por `integration/tep/send/`.

    Una fila por envío de una OP x origen x centro de trabajo. Log de
    auditoría: no hereda de `ActiveModel`/`UserAuditModel` (no se edita ni se
    borra; solo cambia `status`). Sin restricción de unicidad: una misma
    combinación puede enviarse más de una vez (reintentos, envíos parciales).
    """

    op_rowid = models.BigIntegerField(db_index=True)
    op_number = models.IntegerField(null=True, blank=True)
    op_type = models.CharField(max_length=10, null=True, blank=True)
    origin_id = models.IntegerField()
    work_center_rowid = models.BigIntegerField()

    total_recorded = models.IntegerField()
    recorded_quantity_per_piece = models.DecimalField(max_digits=18, decimal_places=4)
    sent_quantity = models.DecimalField(max_digits=18, decimal_places=4)
    hours = models.DecimalField(max_digits=10, decimal_places=4)

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

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tep_submissions",
    )

    class Meta:
        db_table = "integration_tep_submission"
        ordering = ["-created_at"]

    def __str__(self):
        return f"TEP OP {self.op_rowid} / WC {self.work_center_rowid} [{self.status}]"
