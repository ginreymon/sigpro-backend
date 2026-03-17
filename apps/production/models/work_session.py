from django.db import models
from django.conf import settings
from core.models.audit_model import TimeAuditModel, UserAuditModel
from .work_shift import WorkShift
from .module import Module
from django.utils import timezone
from django.db.models import Q


class WorkSession(TimeAuditModel, UserAuditModel):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="work_sessions"
    )

    work_shift = models.ForeignKey(
        WorkShift, on_delete=models.PROTECT, related_name="work_sessions"
    )

    module = models.ForeignKey(
        Module, on_delete=models.PROTECT, related_name="work_sessions"
    )

    employees_snapshot = models.JSONField(default=list, blank=True)

    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    total_time = models.DurationField(null=True, blank=True)

    is_closed = models.BooleanField(default=False)

    class Meta:
        ordering = ["started_at"]
        indexes = [
            models.Index(fields=["started_at"]),
            models.Index(fields=["user", "is_closed"]),
            models.Index(fields=["module"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(is_closed=False),
                name="unique_active_session_per_user",
            )
        ]

    def close_session(self):
        if self.is_closed:
            return

        if not self.started_at:
            raise ValueError("Session has no start time")

        self.ended_at = timezone.now()
        self.total_time = self.ended_at - self.started_at
        self.is_closed = True

        self.save(update_fields=["ended_at", "total_time", "is_closed"])

    def save(self, *args, **kwargs):
        if self.started_at and self.ended_at and not self.is_closed:
            self.total_time = self.ended_at - self.started_at
            self.is_closed = True

        super().save(*args, **kwargs)
