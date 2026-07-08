from django.db import models
from core.models import AuditModel


class StampingMachineType(AuditModel):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
