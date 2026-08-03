from django.db import models
from core.models import AuditModel


class StampingStampTypeDescription(AuditModel):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "stamping_stamping_stamp_type_description"
        ordering = ['name']

    def __str__(self):
        return self.name
