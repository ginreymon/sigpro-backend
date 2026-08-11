from django.db import models
from .sheet_measurement_base import SheetMeasurementBase


class SheetMeasurement(SheetMeasurementBase):
    """
    Garment measurement definition per technical sheet.
    Source: FichasTecnicas_Produccion_Reymon.Ficha.MedidasPrendas
    Linked to TechnicalSheet via sheet_id (MedidasPrendas.FichaID = TechnicalSheet.rowid).
    """

    # rowid, sheet_id, measurement, order inherited from SheetMeasurementBase
    tolerance = models.TextField(null=True, blank=True)         # MedidasPrendas.Tolerancia

    class Meta:
        db_table = "catalog_sheet_measurement"
        ordering = ["sheet_id"]

    def __str__(self):
        return f"{self.sheet_id} - {self.measurement}"
