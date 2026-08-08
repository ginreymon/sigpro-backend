from django.db import models
from core.models import AuditModel


class ProductionArea(AuditModel):

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    core_module = models.OneToOneField(
        "core.Module",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="production_area",
    )
    class Meta:
        db_table = "production_production_area"
        ordering = ["name"]

    @property
    def cost_centers(self):
        return list(self.cost_center_links.values_list("cost_center_rowid", flat=True))

    def __str__(self):
        return self.name
