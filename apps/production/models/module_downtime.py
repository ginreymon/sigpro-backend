from django.db import models
from django.db.models import Q, CheckConstraint
from core.models.audit_model import TimeAuditModel, UserAuditModel
from apps.production.models.module import Module
from apps.production.models.production_record import ProductionRecord


class ModuleDowntime(TimeAuditModel, UserAuditModel):

    module = models.ForeignKey(
        Module, on_delete=models.CASCADE, related_name="module_downtimes"
    )

    # Paro auto-generado al registrar producción/estampación con hora inicial/
    # final manual (cubre el hueco previo a ese registro) — NULL para paros
    # reales de máquina, registrados de forma independiente. A lo sumo uno de
    # los dos puede estar seteado (ver constraint más abajo); nunca los dos,
    # porque un módulo es de producción o de estampación, no ambos.
    production_record = models.ForeignKey(
        ProductionRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="module_downtimes",
    )

    stamping_record = models.ForeignKey(
        "stamping.StampingRecord",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="module_downtimes",
    )

    # Reason of the downtime (free text, or a fixed name for the auto-generated batch downtime).
    name = models.CharField(max_length=255)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "production_module_downtime"
        ordering = ["start_time", "end_time"]
        constraints = [
            CheckConstraint(
                name="module_downtime_single_record_link",
                condition=~(
                    Q(production_record__isnull=False)
                    & Q(stamping_record__isnull=False)
                ),
            ),
        ]

    @property
    def duration(self):
        if self.end_time:
            return self.end_time - self.start_time
        return None
