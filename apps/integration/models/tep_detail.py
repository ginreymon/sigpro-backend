from django.db import models

from core.models import TimeAuditModel, UserAuditModel


class TepDetail(UserAuditModel, TimeAuditModel):
    """Detalle TEP (registro 880) enviado a SIESA por `integration/tep/send/`.

    Columnas alineadas con el item de `details` del request (nombres de la
    API, en inglés) y con `DETAIL_LAYOUT` de `builders/tep.py`. Sin
    restricción de unicidad: una misma OP x operación x centro de trabajo
    puede enviarse más de una vez.
    """

    op_document_type_id = models.CharField(max_length=5, default="OP")
    op_document_number = models.IntegerField(db_index=True)
    operation_number = models.IntegerField()
    operation_work_center_id = models.CharField(max_length=15)
    completed_quantity = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    class Meta:
        db_table = "integration_tep_detail"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.op_document_type_id} {self.op_document_number} "
            f"op {self.operation_number} / {self.operation_work_center_id}"
        )
