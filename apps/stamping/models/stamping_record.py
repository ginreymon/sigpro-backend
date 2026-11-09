from django.db import models
from apps.common.models.tep_integration_record import TepIntegrationRecord
from apps.common.models.op_work_record import OpWorkRecord
from .stamping_reference_sam import StampingReferenceSam


class StampingRecord(OpWorkRecord, TepIntegrationRecord):

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
