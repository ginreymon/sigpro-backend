from django.db import models
from .sheet_measurement_detail_base import SheetMeasurementDetailBase


class SheetElasticCutDetail(SheetMeasurementDetailBase):
    """
    Per-size detail values for an elastic cut measurement.
    Source: FichasTecnicas_Produccion_Reymon.Ficha.DetalleCorteElastico
    Linked to SheetElasticCut via sheet_elastic_cut_id (DetalleCorteElastico.CorteElasticoID = SheetElasticCut.rowid).
    """

    # rowid, value, unit, size inherited from SheetMeasurementDetailBase
    sheet_elastic_cut_id = models.IntegerField()     # DetalleCorteElastico.CorteElasticoID → SheetElasticCut.rowid

    class Meta(SheetMeasurementDetailBase.Meta):
        ordering = ["sheet_elastic_cut_id", "size"]

    def __str__(self):
        return f"{self.sheet_elastic_cut_id} - {self.size} - {self.value}"
