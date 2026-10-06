from django.db import models
from apps.integration.models.op_record import OpRecord
from apps.production.models.work_session_activity import WorkSessionActivity


class ProductionRecord(OpRecord):

    sku_rowid = models.BigIntegerField()
    work_session_activity = models.ForeignKey(
        WorkSessionActivity, on_delete=models.CASCADE, related_name="production_records"
    )

    planned_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    scrap_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    rejected_quantity = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "production_production_record"
        ordering = [
            "start_time",
            "end_time",
            "sku_rowid",
        ]

    def __str__(self):
        return (
            f"SKU {self.sku_rowid} | "
            f"Session {self.work_session_activity.created_at} | "
            f"Completed {self.completed_quantity}"
        )
