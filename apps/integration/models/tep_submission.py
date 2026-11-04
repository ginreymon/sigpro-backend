from django.db import models

from core.models import TimeAuditModel, UserAuditModel


class TepSubmissionStatus(models.TextChoices):
    PENDING = "pending", "Pendiente"
    SENT = "sent", "Enviado"
    FAILED = "failed", "Fallido"


class TepSubmission(UserAuditModel, TimeAuditModel):
    """Header (record 450) of what is sent to SIESA through
    `integration/tep/send/`, plus the send result.

    One row per POST. Columns match the request `header` (API names, in
    English) and `HEADER_LAYOUT` in `builders/tep.py`; the SIESA header
    `status` (0/1/2) is stored as `document_status` so it does not clash with
    the submission `status`. `details` items are stored in `TepDetail`. Saved
    also when SIESA rejects the submission.
    (document_type_id, document_number) is unique (legacy rows with number 0
    are excluded); failed submissions keep their number, a retry gets a new one.
    """

    company_id = models.IntegerField()
    auto_consecutive = models.SmallIntegerField(default=1)
    operation_center_id = models.CharField(max_length=3)
    document_type_id = models.CharField(max_length=3, default="TPW")
    document_number = models.IntegerField()
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
        constraints = [
            # 0 is the ONLY value allowed to repeat: legacy rows created before
            # document numbering existed all carry document_number = 0.
            # Every real document number must be unique per document type.
            models.UniqueConstraint(
                fields=["document_type_id", "document_number"],
                # SQL Server filtered indexes reject NOT; use a positive predicate.
                condition=models.Q(document_number__gt=0),
                name="uq_tep_submission_doc_type_number",
            )
        ]

    def __str__(self):
        return f"TEP {self.document_type_id} {self.document_number} [{self.status}]"
