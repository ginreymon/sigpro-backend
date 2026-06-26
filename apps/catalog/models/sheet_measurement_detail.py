from django.db import models
from .sheet_measurement_detail_base import SheetMeasurementDetailBase


class SheetMeasurementDetail(SheetMeasurementDetailBase):
    """
    Per-size measurement values for a garment measurement.
    Source: FichasTecnicas_Produccion_Reymon.Ficha.DetalleMedidasPrendas
    Linked to SheetMeasurement via sheet_measurement_id (DetalleMedidasPrendas.MedidasPrendasID = SheetMeasurement.rowid).
    """

    # rowid, value, unit, size inherited from SheetMeasurementDetailBase
    sheet_measurement_id = models.IntegerField()     # DetalleMedidasPrendas.MedidasPrendasID → SheetMeasurement.rowid

    class Meta(SheetMeasurementDetailBase.Meta):
        ordering = ["sheet_measurement_id", "size"]

    def __str__(self):
        return f"{self.sheet_measurement_id} - {self.size} - {self.value}"
