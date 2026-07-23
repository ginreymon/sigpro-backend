from django.db import models
from django.utils import timezone
from core.models.audit_model import TimeAuditModel, UserAuditModel
from apps.production.models.work_session_activity import WorkSessionActivity
from .stamping_reference_sam import StampingReferenceSam


class StampingRecord(TimeAuditModel, UserAuditModel):

    op_rowid = models.BigIntegerField(null=True, blank=True)
    op_number = models.IntegerField(null=True, blank=True)
    op_type = models.CharField(max_length=10, null=True, blank=True)

    work_session_activity = models.ForeignKey(
        WorkSessionActivity, on_delete=models.CASCADE, related_name="stamping_records"
    )

    stamping_reference_sam = models.ForeignKey(
        StampingReferenceSam,
        on_delete=models.PROTECT,
        related_name="stamping_records",     
    )

    ordered_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    completed_quantity = models.DecimalField(max_digits=10, decimal_places=2)

    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = [
            "start_time",
            "end_time",
        ]

    def close(self):
        if self.end_time:
            return
        self.end_time = timezone.now()
        self.save(update_fields=["end_time"])

    def __str__(self):
        reference = self.stamping_reference_sam.identification if self.stamping_reference_sam else "N/A"
        return (
            f"{reference} | "
            f"Session {self.work_session_activity.created_at} | "
            f"Completed {self.completed_quantity}"
        )
