from django.db import models
from core.models import AuditModel


class StampingLocation(AuditModel):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "stamping_stamping_location"
        ordering = ['name']

    def __str__(self):
        return self.name
