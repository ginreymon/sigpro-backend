from django.db import models
from core.models import AuditModel
from .stamping_machine_type import StampingMachineType


class StampingMachine(AuditModel):
    name = models.CharField(max_length=100, unique=True)
    machine_type = models.ForeignKey(
        StampingMachineType, on_delete=models.PROTECT, related_name='machines'
    )

    class Meta:
        db_table = "stamping_stamping_machine"
        ordering = ['name']

    def __str__(self):
        return self.name
