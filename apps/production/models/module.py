from django.db import models
from core.models import AuditModel


class Module(AuditModel):

    name = models.CharField(max_length=255)
    number = models.IntegerField()
    operator_count = models.IntegerField()
    location = models.CharField(max_length=255)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"{self.number} - {self.name}"
