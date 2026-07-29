from django.db import models
from core.models.audit_model import TimeAuditModel, UserAuditModel


class AuditRecord(TimeAuditModel, UserAuditModel):

    op_number = models.IntegerField(null=True, blank=True)
    op_rowid = models.BigIntegerField(null=True, blank=True)
    op_type = models.CharField(max_length=10, null=True, blank=True)

    color = models.CharField(max_length=100)
    sku_rowids = models.JSONField()
    ordered_quantity = models.PositiveIntegerField()
    audited_quantity = models.PositiveIntegerField()
    total_op_quantity = models.PositiveIntegerField()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"OP {self.op_number} | {self.color} | ordenada {self.ordered_quantity} | auditada {self.audited_quantity}"
