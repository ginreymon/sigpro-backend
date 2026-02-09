from django.db import models
from django.conf import settings
from core.models.audit_model import TimeAuditModel, UserAuditModel
from .work_shift import WorkShift
from django.utils import timezone


class WorkSession(TimeAuditModel, UserAuditModel):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="work_sessions"
    )

    work_shift = models.ForeignKey(
        WorkShift, on_delete=models.PROTECT, related_name="work_sessions"
    )

    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    total_time = models.DurationField(null=True, blank=True)

    is_closed = models.BooleanField(default=False)

    class Meta:
        ordering = ["started_at"]

    def close_session(self):
        if self.started_at:
            self.ended_at = timezone.now()
            self.save()

    def save(self, *args, **kwargs):
        if self.started_at and self.ended_at:
            self.total_time = self.ended_at - self.started_at
            self.is_closed = True

        super().save(*args, **kwargs)
