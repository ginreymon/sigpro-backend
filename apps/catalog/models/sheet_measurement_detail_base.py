from django.db import models
from core.models import AuditModel, LocalBaseModel


class SheetMeasurementDetailBase(AuditModel, LocalBaseModel):
    """
    Abstract base for per-size detail models linked to sheet measurement parents.
    Subclasses add their own sheet_xxx_id FK field.
    """

    value = models.TextField(null=True, blank=True)
    unit = models.CharField(max_length=50, null=True, blank=True)
    size = models.CharField(max_length=100, null=True, blank=True)

    class Meta(AuditModel.Meta):
        abstract = True
