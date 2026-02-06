from django.db import models
from django.conf import settings
from core.models.audit_model import TimeAuditModel, UserAuditModel
from .work_shift import WorkShift


class WorkSession(TimeAuditModel, UserAuditModel):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="work_sessions"
    )

    work_shift = models.ForeignKey(
        WorkShift, on_delete=models.PROTECT, related_name="work_sessions"
    )

    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)

    is_closed = models.BooleanField(default=False)

    class Meta:
        ordering = ["started_at"]
