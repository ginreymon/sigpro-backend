from django.db import models
from core.models import AuditModel
from .work_center_local import WorkCenterLocal
from .production_area import ProductionArea


class Module(AuditModel):

    name = models.CharField(max_length=255,unique=True)
    number = models.IntegerField(unique=True)
    operator_count = models.IntegerField()

    work_center = models.ForeignKey(
        WorkCenterLocal,
        on_delete=models.PROTECT,
        related_name="modules",
        null=False,
        blank=False,
    )

    location = models.ForeignKey(
        ProductionArea,
        on_delete=models.PROTECT,
        related_name="modules",
        null=True,
        blank=True,
    )

    # Habilita/deshabilita el registro de producción/estampación con
    # duración manual (POST .../manual-duration/) para este módulo. Apagado
    # por defecto: es una función nueva, opcional por módulo.
    allows_manual_duration_entry = models.BooleanField(default=False)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"{self.number} - {self.name}"
