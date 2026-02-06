from django.db import models
from django.db.models import Q, CheckConstraint
from core.models.audit_model import TimeAuditModel, UserAuditModel
from .work_break import WorkBreak
from .work_session import WorkSession


class WorkBreakRecord(TimeAuditModel, UserAuditModel):

    session = models.ForeignKey(
        WorkSession, on_delete=models.CASCADE, related_name="work_break_records"
    )

    work_break = models.ForeignKey(
        WorkBreak,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="work_break_records",
    )

    custom_reason = models.TextField(null=True, blank=True)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["start_time", "end_time"]
        constraints = [
            CheckConstraint(
                name="work_break_or_custom_reason",
                condition=(
                    Q(work_break__isnull=False, custom_reason__isnull=True)
                    | Q(work_break__isnull=True)
                    & Q(custom_reason__isnull=False)
                    & ~Q(custom_reason="")
                ),
            )
        ]
