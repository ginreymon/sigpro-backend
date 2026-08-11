from django.db import models
from core.models import AuditModel, LocalBaseModel


class TechnicalSheetImage(AuditModel, LocalBaseModel):
    """
    Local copy of [FichasTecnicas_Produccion_Reymon].[Ficha].[FichaImagen].
    Synced via stored procedure. Linked to TechnicalSheet via sheet_id (FichaID).
    """

    sheet_id = models.IntegerField()
    file_path = models.TextField()

    class Meta:
        db_table = "catalog_technical_sheet_image"
        ordering = ["sheet_id"]

    def __str__(self):
        return f"{self.sheet_id} — {self.file_path}"
