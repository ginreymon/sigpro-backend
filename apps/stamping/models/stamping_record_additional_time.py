from django.db import models
from core.models.audit_model import TimeAuditModel, UserAuditModel
from .stamping_record import StampingRecord
from .additional_stamping_time import AdditionalStampingTime


class StampingRecordAdditionalTime(TimeAuditModel, UserAuditModel):

    stamping_record = models.ForeignKey(
        StampingRecord, on_delete=models.CASCADE, related_name="additional_time_selections"
    )

    additional_stamping_time = models.ForeignKey(
        AdditionalStampingTime, on_delete=models.PROTECT, related_name="stamping_record_selections"
    )

    count = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "stamping_stamping_record_additional_time"
        constraints = [
            models.UniqueConstraint(
                fields=["stamping_record", "additional_stamping_time"],
                name="unique_stamping_record_additional_time",
            )
        ]

    def __str__(self):
        return f"{self.stamping_record_id} - {self.additional_stamping_time.code_number} x{self.count}"
