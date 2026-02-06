from django.db import models
from core.models.audit_model import AuditModel


class WorkBreak(AuditModel):

    name = models.CharField(max_length=255)
    description = models.TextField()
    duration = models.DurationField()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - {self.duration}"
