from django.db import models
from apps.production.models.op_record import OpRecord
from apps.production.models.work_session_activity import WorkSessionActivity
from .stamping_reference_sam import StampingReferenceSam


class StampingRecord(OpRecord):

    work_session_activity = models.ForeignKey(
        WorkSessionActivity, on_delete=models.CASCADE, related_name="stamping_records"
    )

    stamping_reference_sam = models.ForeignKey(
        StampingReferenceSam,
        on_delete=models.PROTECT,
        related_name="stamping_records",     
    )

    class Meta:
        db_table = "stamping_stamping_record"
        ordering = [
            "start_time",
            "end_time",
        ]

    def __str__(self):
        reference = self.stamping_reference_sam.reference_code if self.stamping_reference_sam else "N/A"
        return (
            f"{reference} | "
            f"Session {self.work_session_activity.created_at} | "
            f"Completed {self.completed_quantity}"
        )
