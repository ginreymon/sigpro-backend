from django.db import models
from core.models.audit_model import AuditModel


class WorkBreak(AuditModel):

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    duration = models.DurationField()

    class Meta:
        db_table = "production_work_break"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - {self.duration}"
