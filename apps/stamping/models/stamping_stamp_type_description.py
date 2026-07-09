from django.db import models
from core.models import AuditModel


class StampingStampTypeDescription(AuditModel):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
