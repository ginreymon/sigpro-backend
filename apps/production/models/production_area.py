from django.db import models
from core.models import AuditModel


class ProductionArea(AuditModel):

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    core_module = models.ForeignKey(
        "core.Module",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        unique=True,
        related_name="production_area",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
