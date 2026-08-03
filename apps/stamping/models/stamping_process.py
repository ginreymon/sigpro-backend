from django.db import models
from core.models import AuditModel
from .stamping_machine import StampingMachine


class StampingProcess(AuditModel):
    name = models.CharField(max_length=100, unique=True)
    machine = models.ForeignKey(
        StampingMachine, on_delete=models.PROTECT, related_name='processes', null=True, blank=True
    )

    class Meta:
        db_table = "stamping_stamping_process"
        ordering = ['name']

    def __str__(self):
        return self.name
