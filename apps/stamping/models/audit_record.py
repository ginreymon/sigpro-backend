from django.db import models
from django.db.models import Sum
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

    @property
    def total_audited_quantity(self):
        return AuditRecord.objects.filter(
            op_number=self.op_number,
            op_rowid=self.op_rowid,
            op_type=self.op_type,
            total_op_quantity=self.total_op_quantity,
        ).aggregate(total=Sum('audited_quantity'))['total'] or 0

    @property
    def matches_total(self):
        return self.total_audited_quantity == self.total_op_quantity
