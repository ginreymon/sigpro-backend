from django.db import models
from core.models.audit_model import AuditModel


class WorkShift(AuditModel):
    name = models.CharField(max_length=255)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"
