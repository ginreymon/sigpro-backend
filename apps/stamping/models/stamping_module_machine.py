from django.db import models
from core.models import AuditModel
from apps.production.models import Module
from .stamping_machine import StampingMachine


class StampingModuleMachine(AuditModel):
    module = models.OneToOneField(
        Module, on_delete=models.CASCADE, related_name='stamping_machine_assignment'
    )
    machine = models.OneToOneField(
        StampingMachine, on_delete=models.PROTECT, related_name='module_assignment'
    )
    # Módulos con esta máquina buscan OP vía
    # /stamping/production-orders/processes/ (sp_ordenes_produccion_proceso_json)
    # en vez del endpoint genérico de production-orders/detail.
    uses_processes_search = models.BooleanField(default=False)

    class Meta:
        db_table = "stamping_stamping_module_machine"
        ordering = ['module__number']

    def __str__(self):
        return f"{self.module.name} - {self.machine.name}"
