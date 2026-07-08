from django.db import models
from core.models import AuditModel


class StampingReferenceSam(AuditModel):
    rowid_item = models.BigIntegerField(db_index=True)  # production_skuitemlocal.rowid_item
    identification = models.CharField(max_length=50, unique=True)  # excel col A (REFERENCIA)
    machine = models.CharField(max_length=100)
    people_count = models.IntegerField()
    piece = models.CharField(max_length=255)
    stamped_pieces = models.IntegerField()
    location = models.CharField(max_length=255, null=True, blank=True)
    stamp_type_description = models.CharField(max_length=255, null=True, blank=True)
    technique = models.CharField(max_length=255, null=True, blank=True)
    garment_type = models.CharField(max_length=100, null=True, blank=True)
    fabric_type = models.CharField(max_length=100, null=True, blank=True)
    line = models.CharField(max_length=100, null=True, blank=True)
    brand = models.CharField(max_length=100, null=True, blank=True)
    collection = models.CharField(max_length=100, null=True, blank=True)
    process = models.CharField(max_length=255, null=True, blank=True)
    frames = models.IntegerField(null=True, blank=True)
    inks = models.IntegerField(null=True, blank=True)
    prints = models.IntegerField(null=True, blank=True)
    pieces_per_board = models.IntegerField(null=True, blank=True)
    layout_form = models.CharField(max_length=100, null=True, blank=True)
    pre_dried = models.IntegerField(null=True, blank=True)
    sam_single_person = models.DecimalField(max_digits=10, decimal_places=4)  
    tasks_per_hour = models.IntegerField()
  

    class Meta:
        ordering = ["identification"]

    def __str__(self):
        return f"{self.identification} - {self.process}"
