from django.db import models

from core.models import TimeAuditModel, UserAuditModel

from .tep_submission import TepSubmission


class TepDetail(UserAuditModel, TimeAuditModel):
    """Detalle/movimiento (registro 880) de un `TepSubmission`.

    Una fila por item de `details` del request. Columnas alineadas con ese
    item (nombres de la API, en inglés) y con `DETAIL_LAYOUT` de
    `builders/tep.py`. `company_id`, `operation_center_id` y el documento TEP
    se heredan del encabezado (`submission`), por eso no se repiten aquí.
    """

    submission = models.ForeignKey(TepSubmission, on_delete=models.CASCADE, related_name="details")

    record_number = models.IntegerField()
    op_document_type_id = models.CharField(max_length=3, default="OP")
    op_document_number = models.IntegerField(db_index=True)
    item_id = models.IntegerField(default=0)
    item_reference = models.CharField(max_length=50, blank=True, default="")
    barcode = models.CharField(max_length=20, blank=True, default="")
    extension1_id = models.CharField(max_length=20, blank=True, default="")
    extension2_id = models.CharField(max_length=20, blank=True, default="")
    operation_number = models.IntegerField()
    operation_work_center_id = models.CharField(max_length=15)
    hour_type = models.SmallIntegerField(default=0)
    labor_id = models.CharField(max_length=15, blank=True, default="")
    machine_id = models.CharField(max_length=15, blank=True, default="")
    operation_completed = models.SmallIntegerField(default=0)
    completed_quantity = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    rework_quantity = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    rejected_quantity = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    rejection_reason_id = models.CharField(max_length=2, blank=True, default="")
    start_time = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    end_time = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    stop_reason_id = models.CharField(max_length=2, blank=True, default="")
    notes = models.CharField(max_length=255, blank=True, default="")
    operator_count = models.SmallIntegerField(default=1)

    class Meta:
        db_table = "integration_tep_detail"
        ordering = ["submission_id", "record_number"]

    def __str__(self):
        return (
            f"{self.op_document_type_id} {self.op_document_number} "
            f"op {self.operation_number} / {self.operation_work_center_id}"
        )
