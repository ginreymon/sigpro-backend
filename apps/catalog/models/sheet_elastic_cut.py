from django.db import models
from .sheet_measurement_base import SheetMeasurementBase


class SheetElasticCut(SheetMeasurementBase):
    """
    Elastic cut observations per technical sheet.
    Source: FichasTecnicas_Produccion_Reymon.Ficha.CorteElastico
    Linked to TechnicalSheet via sheet_id (CorteElastico.FichaID = TechnicalSheet.rowid).
    """

    # rowid → CorteElastico.Rowid
    # sheet_id → CorteElastico.FichaID → TechnicalSheet.rowid
    # measurement → CorteElastico.Medida
    # order → CorteElastico.Orden    

    class Meta(SheetMeasurementBase.Meta):
        ordering = ["sheet_id"]

    def __str__(self):
        return f"{self.sheet_id} - {self.measurement}"
