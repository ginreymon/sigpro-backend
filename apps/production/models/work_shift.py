from django.db import models
from core.models.audit_model import AuditModel
from .production_area import ProductionArea


class WorkShift(AuditModel):
    name = models.CharField(max_length=255, unique=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    app_module = models.ForeignKey(
        "core.Module",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="work_shifts",
    )
    location = models.ForeignKey(
        ProductionArea,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="work_shifts",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"
