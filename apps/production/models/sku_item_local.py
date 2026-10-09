from django.db import models
from django.db.models import CharField, OuterRef, Subquery
from core.models import TimeAuditModel, ActiveModel, LocalBaseModel


class SkuItemLocal(TimeAuditModel, ActiveModel, LocalBaseModel):
    """
    Represents a SKU (item with extensions: reference + size + color)
    Source: t121_mc_items_extensiones + t120_mc_items (reymon)
    """

    # --- Identifiers ---
    # rowid                                                                # t121_mc_items_extensiones.f121_rowid SKU rowid
    rowid_item = models.BigIntegerField(db_index=True)                    # t120_mc_items.f120_rowid reference rowid
    barcode    = models.CharField(max_length=50, blank=True, null=True)   # f121_id_barras_principal

    # --- Item classification ---
    reference   = models.CharField(max_length=50)                          # f120_referencia
    description = models.CharField(max_length=255)                         # f120_descripcion
    size        = models.CharField(max_length=20, blank=True, null=True)  # f121_id_ext1_detalle
    color       = models.CharField(max_length=20, blank=True, null=True)  # f121_id_ext2_detalle
    inv_type    = models.CharField(max_length=10, blank=True, null=True)  # f120_id_tipo_inv_serv
    size_key    = models.CharField(max_length=20, blank=True, null=True)  # f117_descripcion_corta

    # --- Units ---
    inventory_unit = models.CharField(max_length=10, blank=True, null=True)  # f120_id_unidad_inventario
    order_unit     = models.CharField(max_length=10, blank=True, null=True)  # f120_id_unidad_orden
    packing_unit   = models.CharField(max_length=10, blank=True, null=True)  # f120_id_unidad_empaque

    # --- Installation / logistics ---
    replenishment_time = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # f132_mf_tiempo_repo_fijo
    lot_size           = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # f132_mf_tamano_lote
    safety_stock       = models.DecimalField(max_digits=14, decimal_places=4, blank=True, null=True)  # f132_mf_stock_segur_estatico

    # --- Status ---
    status     = models.SmallIntegerField(blank=True, null=True)           # f121_ind_estado
    sku_status = models.CharField(max_length=100, blank=True, null=True)  # f741_descripcion

    # --- Prices ---
    cost            = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)  # list AVC
    suggested_price = models.DecimalField(max_digits=18, decimal_places=4, blank=True, null=True)  # list APS

    # --- Criteria / classifications (plan) ---
    brand          = models.CharField(max_length=100, blank=True, null=True)  # plan 100
    line           = models.CharField(max_length=100, blank=True, null=True)  # plan 200
    group          = models.CharField(max_length=100, blank=True, null=True)  # plan 300
    subgroup       = models.CharField(max_length=100, blank=True, null=True)  # plan 400
    classification = models.CharField(max_length=100, blank=True, null=True)  # plan 500
    sewing         = models.CharField(max_length=100, blank=True, null=True)  # plan 600
    print_design   = models.CharField(max_length=100, blank=True, null=True)  # plan 900
    license        = models.CharField(max_length=100, blank=True, null=True)  # plan DIS
    collection     = models.CharField(max_length=100, blank=True, null=True)  # plan LIN
    world          = models.CharField(max_length=100, blank=True, null=True)  # plan MUN
    channel        = models.CharField(max_length=100, blank=True, null=True)  # plan CAN
    promotion      = models.CharField(max_length=100, blank=True, null=True)  # plan PRO
    priority       = models.CharField(max_length=100, blank=True, null=True)  # plan PRI
    pieces_per_set = models.CharField(max_length=100, blank=True, null=True)  # plan UND

    class Meta:
        db_table = "production_sku_item_local"
        ordering = ["rowid", "rowid_item", "reference", "size", "color"]

    def __str__(self):
        return f"{self.reference} - {self.size} / {self.color}"

    @classmethod
    def reference_subquery(cls, outer_field="rowid_item"):
        """Subquery returning the reference of the first non-deleted SKU whose
        rowid_item matches the outer queryset's `outer_field`."""
        return Subquery(
            cls.objects.filter(
                rowid_item=OuterRef(outer_field),
                is_deleted=False,
            ).order_by().values("reference")[:1],
            output_field=CharField(),
        )

    @classmethod
    def map_by_rowid_item(cls, rowid_items):
        """One SkuItemLocal per rowid_item (first match), keyed by rowid_item. Batch fetch to avoid N+1."""
        skus = cls.objects.filter(
            rowid_item__in=rowid_items, is_deleted=False
        ).order_by("rowid_item", "id")
        mapping = {}
        for sku in skus:
            mapping.setdefault(sku.rowid_item, sku)
        return mapping
