from django.db import models
from core.models.audit_model import TimeAuditModel, UserAuditModel, ActiveModel
from .work_session import WorkSession 
from .module import Module
from django.utils import timezone
from django.db.models import Q


class WorkSessionActivity(TimeAuditModel, UserAuditModel, ActiveModel):

    module = models.ForeignKey(
        Module, on_delete=models.PROTECT, related_name="activities"
    )

    work_session = models.ForeignKey(
        WorkSession, on_delete=models.PROTECT, related_name="work_session_activities"
    ) 

    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)     
   
    class Meta:
        ordering = ["started_at"]
        indexes = [
            models.Index(fields=["started_at"]),
            models.Index(fields=["work_session"]),
            models.Index(fields=["module"]),
            models.Index(fields=["work_session", "ended_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["work_session"],
                condition=Q(ended_at__isnull=True),
                name="unique_active_activity_per_session",
            )
        ]

    @property
    def total_time_minutes(self):
        if not self.ended_at:
            return None

        delta = self.ended_at - self.started_at
        return delta.total_seconds() / 60


    def close(self):       
        if self.ended_at:
            return

        self.ended_at = timezone.now()       
        self.is_active = False

        self.save(update_fields=["ended_at", "is_active"])

    def save(self, *args, **kwargs):
        if self.ended_at:           
            self.is_active = False

        super().save(*args, **kwargs)

    def __str__(self):
        return f"WorkSession {self.work_session.id} - Module {self.module.id} ({self.started_at})"