from django.db import models
from core.models import TimeAuditModel, ActiveModel
from apps.production.models.work_center_local import WorkCenterLocal
from apps.production.models.production_area import ProductionArea


class WorkCenterProductionArea(TimeAuditModel, ActiveModel):
    """Relación work_center -> production_area: 1 área tiene muchos work
    centers, cada work center pertenece a exactamente 1 área. Orientado a
    dbo.fn_totales_registrados_por_op (origin_id = production_area.id)."""

    work_center = models.OneToOneField(
        WorkCenterLocal,
        on_delete=models.PROTECT,
        related_name="production_area_link",
    )

    production_area = models.ForeignKey(
        ProductionArea,
        on_delete=models.PROTECT,
        related_name="work_centers",
    )

    class Meta:
        db_table = "integration_work_center_production_area"

    def __str__(self):
        return f"{self.work_center.code} -> {self.production_area.name}"
