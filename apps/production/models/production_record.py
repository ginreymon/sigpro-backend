from django.db import models
from apps.common.models.op_record import OpRecord
from apps.common.models.op_work_record import OpWorkRecord


class ProductionRecord(OpWorkRecord, OpRecord):

    sku_rowid = models.BigIntegerField()

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
