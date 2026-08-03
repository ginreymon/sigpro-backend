from django.db import models
from core.models import AuditModel


class ReferenceSam(AuditModel):
    """
    Represents the SAM (Standard Allowed Minutes) per reference item.
    One reference (rowid_item) has one and only one SAM value.
    Linked to SkuItemLocal via rowid_item (reference level, not SKU level).
    """

    rowid_item = models.BigIntegerField(unique=True)  # t120_mc_items.f120_rowid
    sam = models.DecimalField(max_digits=10, decimal_places=4)

    class Meta:
        db_table = "production_reference_sam"
        ordering = ["rowid_item"]

    def __str__(self):
        return f"{self.rowid_item} — SAM: {self.sam} min"

    def get_skus(self):
        from apps.production.models import SkuItemLocal  # avoid circular import

        return SkuItemLocal.objects.filter(rowid_item=self.rowid_item)
