from django.db import models
from core.models import AuditModel, LocalBaseModel


class Collection(AuditModel, LocalBaseModel):
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
