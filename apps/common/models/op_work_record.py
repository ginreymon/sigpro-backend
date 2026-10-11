from django.db import models
from django.utils import timezone
from core.models.audit_model import TimeAuditModel, UserAuditModel


class OpWorkRecord(TimeAuditModel, UserAuditModel):
    """Common work data of the records of a production order
    (ProductionRecord and StampingRecord): work session activity, order
    identification, quantities and times.

    `related_name` uses `app_label` to keep `production_records` /
    `stamping_records` without declaring the FK in each child.

    It must be inherited together with `OpRecord` (common/models/op_record.py), before it:
    `close()` calls `save()`, which resolves to `OpRecord.save` (TEP reset).
    """

    work_session_activity = models.ForeignKey(
        "production.WorkSessionActivity",
        on_delete=models.CASCADE,
        related_name="%(app_label)s_records",
    )

    op_rowid = models.BigIntegerField(null=True, blank=True)
    op_number = models.IntegerField(null=True, blank=True)
    op_type = models.CharField(max_length=10, null=True, blank=True)

    ordered_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    completed_quantity = models.DecimalField(max_digits=10, decimal_places=2)

    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def close(self):
        if self.end_time:
            return
        self.end_time = timezone.now()
        self.save(update_fields=["end_time"])
