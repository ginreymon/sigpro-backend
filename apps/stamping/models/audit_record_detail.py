from django.db import models
from apps.stamping.models.audit_record import AuditRecord


class AuditRecordDetail(models.Model):

    audit_record = models.ForeignKey(AuditRecord, on_delete=models.CASCADE, related_name="details")
    color = models.CharField(max_length=100)
    sku_rowids = models.JSONField()
    ordered_quantity = models.PositiveIntegerField()
    audited_quantity = models.PositiveIntegerField()
    # Manually entered meters equivalent to audited_quantity (kg). Only used by
    # CALANDRA orders (machine type 4); NULL for every other order.
    audited_meters = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "stamping_audit_record_detail"

    def __str__(self):
        return f"{self.color} | ordenada {self.ordered_quantity} | auditada {self.audited_quantity}"

    @property
    def quantities_match(self):
        return self.ordered_quantity == self.audited_quantity
