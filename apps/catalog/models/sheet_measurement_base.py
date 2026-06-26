from django.db import models
from core.models import AuditModel, LocalBaseModel


class SheetMeasurementBase(AuditModel, LocalBaseModel):
    """
    Abstract base for sheet-linked measurement models.
    Subclasses share: rowid (origin PK), sheet_id (FichaID → TechnicalSheet), measurement value.
    """

    sheet_id = models.IntegerField()
    measurement = models.TextField(null=True, blank=True)
    order = models.IntegerField(null=True, blank=True)

    class Meta(AuditModel.Meta):
        abstract = True
