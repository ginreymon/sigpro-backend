from django.db import models
from core.models import AuditModel


class TechnicalSheetStatus(AuditModel):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "catalog_technical_sheet_status"
        ordering = ['name']

    def __str__(self):
        return self.name
