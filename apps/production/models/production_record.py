from django.db import models
from django.utils import timezone
from core.models.audit_model import TimeAuditModel, UserAuditModel
from apps.production.models.work_session_activity import WorkSessionActivity


class ProductionRecord(TimeAuditModel, UserAuditModel):

    sku_rowid = models.BigIntegerField()
    op_rowid = models.BigIntegerField(null=True, blank=True)
    op_number = models.IntegerField(null=True, blank=True)
    op_type = models.CharField(max_length=10, null=True, blank=True)

    work_session_activity = models.ForeignKey(
        WorkSessionActivity, on_delete=models.CASCADE, related_name="production_records"
    )

    ordered_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    planned_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    completed_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    scrap_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    rejected_quantity = models.DecimalField(max_digits=10, decimal_places=2)

    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)    

    class Meta:
        db_table = "production_production_record"
        ordering = [
            "start_time",
            "end_time",
            "sku_rowid",
        ]

    def close(self):
        if self.end_time:
            return
        self.end_time = timezone.now()
        self.save(update_fields=["end_time"])

    def __str__(self):
        return (
            f"SKU {self.sku_rowid} | "
            f"Session {self.work_session_activity.created_at} | "
            f"Completed {self.completed_quantity}"
        )
