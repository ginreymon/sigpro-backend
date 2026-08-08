from django.db import models
from core.models.audit_model import TimeAuditModel, UserAuditModel
from .production_area import ProductionArea
from .work_shift import WorkShift
from .work_session import WorkSession


class WorkShiftSnapshot(TimeAuditModel, UserAuditModel):
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.ForeignKey(
        ProductionArea,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="work_shift_records",
    )
    work_session = models.ForeignKey(
        WorkSession,
        on_delete=models.PROTECT,
        related_name="shift_snapshots",
    )
    work_shift = models.ForeignKey(
        WorkShift,
        on_delete=models.PROTECT,
        related_name="shift_snapshots",
    )

    class Meta:
        db_table = "production_work_shift_snapshot"

    def __str__(self):
        return f"{self.start_time} - {self.end_time}"
