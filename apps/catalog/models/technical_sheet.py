from django.db import models
from core.models import AuditModel, LocalBaseModel


class TechnicalSheet(AuditModel, LocalBaseModel):
    """
    Technical specification (ficha técnica) at reference level.
    Source: FichasTecnicas_Produccion_Reymon.Ficha.FichasTecnicas
    Linked to SkuItemLocal via rowid_item (t120_mc_items.f120_rowid).
    """

    rowid_item = models.BigIntegerField()               # rowid_item (t120_mc_items.f120_rowid)

    # Descriptive
    tariff_code = models.CharField(max_length=70, null=True, blank=True)
    source_model = models.TextField(null=True, blank=True)
    colors = models.TextField(null=True, blank=True)
    status = models.ForeignKey(
        'TechnicalSheetStatus',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="technical_sheets",
    )

    # Versioning
    sheet_version = models.CharField(max_length=50, null=True, blank=True)

    # Relations
    collection_rowid = models.BigIntegerField(null=True, blank=True)

    # Operations / logistics
    operational_route = models.CharField(max_length=250, null=True, blank=True)
    warehouse = models.TextField(null=True, blank=True)
    fabric_warehouse = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "catalog_technical_sheet"
        ordering = ["rowid_item"]

    def __str__(self):
        return str(self.rowid_item)

    def get_skus(self):
        from apps.production.models.sku_item_local import SkuItemLocal
        return SkuItemLocal.objects.filter(rowid_item=self.rowid_item)
