from django.db import models
from core.models.audit_model import TimeAuditModel, UserAuditModel
from .work_session import WorkSession


class ProductionRecord(TimeAuditModel, UserAuditModel):

    sku_rowid = models.BigIntegerField()

    session = models.ForeignKey(
        WorkSession, on_delete=models.CASCADE, related_name="production_records"
    )    

    ordered_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    planned_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    completed_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    scrap_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    rejected_quantity = models.DecimalField(max_digits=10, decimal_places=2)

    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = [
            "start_time",
            "end_time",
            "sku_rowid",
        ]

    def __str__(self):
        return (
            f"SKU {self.sku_rowid} | "     
            f"Session {self.session.created_at} | "
            f"Completed {self.completed_quantity}"
        )
