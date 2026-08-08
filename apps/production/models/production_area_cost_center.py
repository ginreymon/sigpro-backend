
from django.db import models
from core.models import AuditModel
from apps.production.models.production_area import ProductionArea


class ProductionAreaCostCenter(AuditModel):

    production_area = models.ForeignKey(
        ProductionArea, on_delete=models.CASCADE, related_name="cost_center_links"
    )
    # ID crudo de reymon.dbo.t284_co_ccosto (f284_rowid) — sin FK porque no
    # existe maestro local de centros de costo (igual que EmployeeLocal.cost_center_rowid).
    cost_center_rowid = models.IntegerField()

    class Meta:
        db_table = "production_production_area_cost_center"
        unique_together = ("production_area", "cost_center_rowid")
        indexes = [
            models.Index(fields=["production_area", "cost_center_rowid"]),
        ]

    def __str__(self):
        return f"{self.production_area_id} - {self.cost_center_rowid}"
