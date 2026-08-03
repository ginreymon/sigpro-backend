from django.db import models
from django.db.models import Sum
from core.models.audit_model import TimeAuditModel, UserAuditModel


class AuditRecord(TimeAuditModel, UserAuditModel):

    op_number = models.IntegerField(null=True, blank=True)
    op_rowid = models.BigIntegerField(null=True, blank=True)
    op_type = models.CharField(max_length=10, null=True, blank=True)
    total_ordered_quantity = models.PositiveIntegerField()
    is_audited = models.BooleanField(default=False)

    class Meta:
        db_table = "stamping_audit_record"
        ordering = ["-created_at"]

    def __str__(self):
        return f"OP {self.op_number} | total ordenado {self.total_ordered_quantity}"

    @property
    def total_audited_quantity(self):
        from apps.stamping.models.audit_record_detail import AuditRecordDetail

        return AuditRecordDetail.objects.filter(
            audit_record__op_number=self.op_number,
            audit_record__op_rowid=self.op_rowid,
            audit_record__op_type=self.op_type,
            audit_record__total_ordered_quantity=self.total_ordered_quantity,
        ).aggregate(total=Sum('audited_quantity'))['total'] or 0

    @property
    def matches_total(self):
        return self.total_audited_quantity == self.total_ordered_quantity
